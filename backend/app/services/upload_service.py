"""YouTube 업로드 서비스."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.integrations.youtube_api import upload_video
from app.models.enums import JobStatus, StageStatus
from app.models.job import Job
from app.models.upload_record import UploadRecord
from app.services.analytics_service import collect_metrics_stub
from app.services.audit_service import log_action
from app.services.metadata_writer import build_metadata
from app.services.notification_service import notify
from app.services.stage_utils import PipelineError, finish_stage, get_stage, start_stage
from app.services.quota_manager import can_upload, record_upload


async def publish_job(session: AsyncSession, job: Job, settings: Settings) -> dict:
    """QA 승인 후 YouTube 업로드 (또는 dry-run)."""
    allowed = {
        JobStatus.QA_PENDING,
        JobStatus.QA_APPROVED,
        JobStatus.UPLOAD_FAILED,
    }
    if job.status not in allowed:
        raise PipelineError(f"업로드 불가 상태: {job.status.value}")

    if not job.script or not job.render_output or not job.topic_candidate:
        raise PipelineError("대본·렌더·주제가 준비되지 않았습니다.")

    ok, reason = await can_upload(settings)
    if not ok:
        raise PipelineError(reason)

    topic = job.topic_candidate
    metadata = build_metadata(topic, job.script.content)
    video_path = Path(job.render_output.video_uri)

    if not video_path.exists():
        raise PipelineError(f"영상 파일 없음: {video_path}")

    job.status = JobStatus.QA_APPROVED
    upload_stage = get_stage(job, "upload")
    start_stage(upload_stage)
    job.status = JobStatus.UPLOADING

    idempotency_key = f"{job.code}-v{job.script.version}"
    if job.upload_record:
        record = job.upload_record
        record.title = metadata["title"]
        record.description = metadata["description"]
        record.tags = metadata["tags"]
        record.upload_status = "uploading"
    else:
        record = UploadRecord(
            job_id=job.id,
            title=metadata["title"],
            description=metadata["description"],
            tags=metadata["tags"],
            ai_label_applied=metadata["ai_label_applied"],
            privacy_status=settings.pilot_default_privacy,
            upload_status="uploading",
            idempotency_key=idempotency_key,
        )
        session.add(record)

    youtube_video_id: str | None = None
    dry_run = settings.pilot_dry_run_upload

    if dry_run:
        youtube_video_id = f"DRY_RUN_{job.code}"
        record.upload_status = "dry_run"
    else:
        oauth = job.channel.oauth_credential if job.channel else None
        if not oauth:
            upload_stage.status = StageStatus.FAILED
            upload_stage.error_message = "YouTube OAuth 미연결"
            job.status = JobStatus.UPLOAD_FAILED
            await notify(settings, "upload.failed", "OAuth 미연결", job_id=job.code)
            raise PipelineError("YouTube OAuth가 연결되지 않았습니다. Settings에서 연결하세요.")

        try:
            publish_at = job.scheduled_publish_at
            youtube_video_id = await upload_video(
                settings,
                oauth,
                str(video_path),
                metadata["title"],
                metadata["description"],
                metadata["tags"],
                privacy_status=settings.pilot_default_privacy,
                publish_at=publish_at,
            )
            record.upload_status = "completed"
        except Exception as exc:
            upload_stage.status = StageStatus.FAILED
            upload_stage.error_message = str(exc)
            record.upload_status = "failed"
            job.status = JobStatus.UPLOAD_FAILED
            await notify(settings, "upload.failed", str(exc), job_id=job.code)
            raise PipelineError(f"YouTube 업로드 실패: {exc}") from exc

    record.youtube_video_id = youtube_video_id
    finish_stage(upload_stage, youtube_video_id or "")
    job.status = JobStatus.PUBLISHED

    await record_upload(settings)
    await collect_metrics_stub(session, job)
    await log_action(
        session,
        "publish",
        "job",
        job.code,
        {"youtube_video_id": youtube_video_id, "dry_run": dry_run},
    )
    await notify(
        settings,
        "upload.success",
        "업로드 완료",
        job_id=job.code,
        video_id=youtube_video_id or "",
    )

    await session.flush()
    return {
        "job_id": job.code,
        "status": job.status.value,
        "youtube_video_id": youtube_video_id,
        "dry_run": dry_run,
        "title": metadata["title"],
        "privacy_status": settings.pilot_default_privacy,
    }
