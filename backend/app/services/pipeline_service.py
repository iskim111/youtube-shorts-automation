"""E2E 파이프라인: 주제 승인 후 생성 → QA 대기 (Beta: 애셋·자막·템플릿 렌더)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import Settings
from app.models.channel import Channel
from app.models.enums import JobStatus, StageStatus
from app.models.job import Job
from app.models.render_output import RenderOutput
from app.models.script import Script
from app.services.ab_service import assign_ab_variant, assign_template_variant, apply_hook_variant
from app.services.asset_service import fetch_assets_for_job
from app.services.metadata_writer import build_metadata
from app.services.stage_utils import PipelineError, fail_stage, finish_stage, get_stage, start_stage
from app.services.render_engine import extract_thumbnail, render_with_template
from app.services.rights_gate import check_rights
from app.services.script_generator import generate_script
from app.services.subtitle_service import write_srt


def _scene_assets_for_render(
    script_content: dict,
    assets: list,
) -> list[tuple[Path | None, int, str]]:
    scenes = script_content.get("scenes") or []
    by_seq = {
        int(a.asset_metadata.get("scene_seq", 0)): a
        for a in assets
        if a.asset_metadata
    }
    if not by_seq and assets:
        by_seq[1] = assets[0]

    timeline: list[tuple[Path | None, int, str]] = []
    for scene in scenes:
        seq = int(scene.get("seq", len(timeline) + 1))
        duration = int(scene.get("duration_sec", 8))
        asset = by_seq.get(seq)
        if not asset or not asset.storage_uri:
            timeline.append((None, duration, "placeholder"))
            continue
        path = Path(asset.storage_uri)
        kind = asset.asset_metadata.get("media_kind", "video")
        if not path.exists():
            timeline.append((None, duration, "placeholder"))
        else:
            timeline.append((path, duration, kind))
    return timeline


_RERUN_FROM_QA_STATUSES = frozenset({JobStatus.QA_PENDING, JobStatus.QA_APPROVED})


async def run_pipeline_to_qa(session: AsyncSession, job: Job, settings: Settings) -> Job:
    if job.status not in (
        JobStatus.TOPIC_APPROVED,
        JobStatus.SCRIPT_READY,
        JobStatus.QA_HOLD,
        JobStatus.RIGHTS_HOLD,
        *_RERUN_FROM_QA_STATUSES,
    ):
        raise PipelineError(f"파이프라인 실행 불가 상태: {job.status.value}")

    topic = job.topic_candidate
    if not topic:
        raise PipelineError("연결된 주제가 없습니다.")

    job_dir = Path(settings.data_dir) / "jobs" / job.code
    job_dir.mkdir(parents=True, exist_ok=True)

    job.ab_variant = assign_ab_variant(job.code)
    if not job.render_template or job.render_template == "bold_center":
        job.render_template = assign_template_variant(job.code)

    preserve_script = job.status in _RERUN_FROM_QA_STATUSES and bool(
        job.script and job.script.content
    )

    # 1. Script
    script_stage = get_stage(job, "script")
    start_stage(script_stage)

    if preserve_script:
        script_content = job.script.content
        hook_variant = script_content.get("hook") or topic.hook_line
    else:
        job.status = JobStatus.SCRIPT_GENERATING
        hook_variant = apply_hook_variant(topic.hook_line, job.ab_variant or "A")
        script_content = generate_script(topic)
        script_content["hook"] = hook_variant
        if script_content.get("scenes"):
            script_content["scenes"][0]["narration"] = hook_variant
        if job.script:
            job.script.content = script_content
            job.script.duration_estimate_sec = script_content["target_duration_sec"]
            job.script.version += 1
        else:
            job.script = Script(
                job_id=job.id,
                content=script_content,
                duration_estimate_sec=script_content["target_duration_sec"],
            )
            session.add(job.script)

    script_path = job_dir / "script.json"
    script_path.write_text(json.dumps(script_content, ensure_ascii=False, indent=2), encoding="utf-8")
    finish_stage(script_stage, str(script_path))
    job.status = JobStatus.SCRIPT_APPROVED

    # 2. TTS stub
    tts_stage = get_stage(job, "tts")
    start_stage(tts_stage)
    audio_path = job_dir / "audio.mp3"
    audio_path.write_bytes(b"")
    finish_stage(tts_stage, str(audio_path))
    job.status = JobStatus.TTS_READY

    # 3. Asset search (Pexels → Pixabay)
    asset_stage = get_stage(job, "asset")
    start_stage(asset_stage)
    job.status = JobStatus.ASSET_SEARCHING
    assets = await fetch_assets_for_job(
        session, job, topic, settings, job_dir, script_content=script_content
    )
    asset_uri = assets[0].storage_uri if assets and assets[0].storage_uri else "generated:fallback"
    finish_stage(asset_stage, asset_uri)
    job.status = JobStatus.ASSET_READY

    # 4. Rights gate
    rights_stage = get_stage(job, "rights")
    start_stage(rights_stage)
    rights_result = check_rights(topic)
    for asset in assets:
        if asset.license_status == "block":
            rights_result["passed"] = False
            rights_result["hold_reasons"].append("blocked_asset")
    if not rights_result["passed"]:
        fail_stage(rights_stage, ", ".join(rights_result["hold_reasons"]))
        job.status = JobStatus.RIGHTS_HOLD
        job.hold_reason = ", ".join(rights_result["hold_reasons"])
        raise PipelineError(job.hold_reason, stage="rights")
    finish_stage(rights_stage)
    job.status = JobStatus.RIGHTS_PASSED

    # 5. Subtitle SRT
    subtitle_stage = get_stage(job, "subtitle")
    start_stage(subtitle_stage)
    srt_path = job_dir / "subtitles.srt"
    write_srt(script_content, srt_path)
    finish_stage(subtitle_stage, str(srt_path))

    # 6. Render with template
    render_stage = get_stage(job, "render")
    start_stage(render_stage)
    job.status = JobStatus.RENDER_PROCESSING
    video_path = job_dir / "output.mp4"
    duration = min(script_content["target_duration_sec"], settings.max_video_duration_sec)

    scene_assets = _scene_assets_for_render(script_content, assets)

    template = job.render_template or "bold_center"
    ok = render_with_template(
        video_path,
        hook_variant,
        duration,
        template=template,
        srt_path=srt_path,
        scene_assets=scene_assets,
    )
    if not ok:
        fail_stage(render_stage, "영상 렌더 실패")
        raise PipelineError("영상 렌더 실패", stage="render")

    thumb_path = job_dir / "thumbnail.jpg"
    extract_thumbnail(video_path, thumb_path)

    if job.render_output:
        job.render_output.video_uri = str(video_path)
        job.render_output.thumbnail_uri = str(thumb_path) if thumb_path.exists() else None
        job.render_output.duration_sec = duration
    else:
        job.render_output = RenderOutput(
            job_id=job.id,
            video_uri=str(video_path),
            thumbnail_uri=str(thumb_path) if thumb_path.exists() else None,
            duration_sec=duration,
        )
        session.add(job.render_output)

    finish_stage(render_stage, str(video_path))
    job.status = JobStatus.RENDER_READY

    # 7. Thumbnail stage
    thumb_stage = get_stage(job, "thumbnail")
    start_stage(thumb_stage)
    finish_stage(thumb_stage, str(thumb_path) if thumb_path.exists() else None)
    job.status = JobStatus.THUMBNAIL_READY

    # 8. Metadata
    meta_stage = get_stage(job, "metadata")
    start_stage(meta_stage)
    metadata = build_metadata(topic, script_content)
    for asset in assets:
        if asset.source_type in ("pexels", "pixabay") and asset.source_url:
            metadata["description"] += f"\n\n영상 출처: {asset.source_url}"
        if asset.asset_metadata.get("ai_generated"):
            metadata["ai_label_applied"] = True
            metadata["description"] += "\n\n일부 비주얼: AI 생성 콘텐츠"
    meta_path = job_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    finish_stage(meta_stage, str(meta_path))
    job.status = JobStatus.METADATA_APPROVED

    upload_stage = get_stage(job, "upload")
    upload_stage.status = StageStatus.PENDING
    job.status = JobStatus.QA_PENDING

    from app.services.audit_service import log_action

    await log_action(session, "pipeline_complete", "job", job.code, {"status": job.status.value})

    from app.services.auto_publish_service import try_auto_publish

    auto_result = await try_auto_publish(session, job, settings)
    if auto_result:
        from app.services.analytics_service import collect_metrics_stub

        await collect_metrics_stub(session, job)

    await session.flush()
    return job


async def load_job_full(session: AsyncSession, job_code: str) -> Job | None:
    result = await session.execute(
        select(Job)
        .options(
            selectinload(Job.stages),
            selectinload(Job.topic_candidate),
            selectinload(Job.channel).selectinload(Channel.oauth_credential),
            selectinload(Job.script),
            selectinload(Job.render_output),
            selectinload(Job.upload_record),
            selectinload(Job.assets),
        )
        .where(Job.code == job_code)
    )
    return result.scalar_one_or_none()
