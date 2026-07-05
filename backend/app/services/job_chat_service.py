"""Job 결과물 미리보기 + AI 채팅 수정."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings
from app.models.job import Job


def build_job_preview(job: Job, settings: Settings | None = None) -> dict[str, Any]:
    from app.config import get_settings

    settings = settings or get_settings()
    video_uri = job.render_output.video_uri if job.render_output else None
    thumb_uri = job.render_output.thumbnail_uri if job.render_output else None
    metadata = None
    reference = None
    job_dir = Path(settings.data_dir) / "jobs" / job.code
    meta_path = job_dir / "metadata.json"
    if meta_path.exists():
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    ref_path = job_dir / "reference_analysis.json"
    if ref_path.exists():
        reference = json.loads(ref_path.read_text(encoding="utf-8"))
    elif job.topic_candidate and job.topic_candidate.score_breakdown:
        breakdown = job.topic_candidate.score_breakdown
        if breakdown.get("reference_url"):
            reference = {
                "url": breakdown.get("reference_url"),
                "video_id": breakdown.get("reference_video_id"),
                "title": breakdown.get("reference_title"),
                **(breakdown.get("reference_analysis") or {}),
            }

    def media_url(path: str | None, fallback_name: str) -> str | None:
        if path:
            normalized = path.replace("\\", "/")
            if "jobs/" in normalized:
                suffix = normalized.split("jobs/", 1)[1]
                return f"/media/jobs/{suffix}"
        fallback = job_dir / fallback_name
        if fallback.exists() and fallback.stat().st_size > 0:
            return f"/media/jobs/{job.code}/{fallback_name}"
        return None

    return {
        "job_id": job.code,
        "status": job.status.value,
        "hook_line": job.topic_candidate.hook_line if job.topic_candidate else "",
        "script": job.script.content if job.script else None,
        "metadata": metadata,
        "reference": reference,
        "video_url": media_url(video_uri, "output.mp4"),
        "thumbnail_url": media_url(thumb_uri, "thumbnail.jpg"),
        "youtube_video_id": job.upload_record.youtube_video_id if job.upload_record else None,
    }


def _apply_hook_change(script: dict, new_hook: str) -> dict:
    updated = json.loads(json.dumps(script, ensure_ascii=False))
    updated["hook"] = new_hook
    if updated.get("scenes"):
        updated["scenes"][0]["narration"] = new_hook
    return updated


def _apply_scene_change(script: dict, seq: int, narration: str) -> dict:
    updated = json.loads(json.dumps(script, ensure_ascii=False))
    for scene in updated.get("scenes", []):
        if scene.get("seq") == seq:
            scene["narration"] = narration
            break
    return updated


def _rule_based_chat(script: dict, message: str) -> tuple[str, dict | None]:
    msg = message.strip()

    hook_match = re.search(r"훅.*?[:：]\s*(.+)", msg, re.I)
    if hook_match or msg.startswith("훅 "):
        new_hook = hook_match.group(1).strip() if hook_match else msg.replace("훅", "").strip()
        if new_hook:
            return (
                f"훅을 「{new_hook}」(으)로 바꿨어요. Run으로 다시 렌더하세요.",
                _apply_hook_change(script, new_hook),
            )

    scene_match = re.search(r"장면\s*(\d+).*?[:：]\s*(.+)", msg, re.I)
    if scene_match:
        seq = int(scene_match.group(1))
        text = scene_match.group(2).strip()
        return f"장면 {seq} 나레이션을 수정했어요.", _apply_scene_change(script, seq, text)

    if "대본" in msg or "보여" in msg:
        scenes = script.get("scenes", [])
        summary = "\n".join(f"{s.get('seq')}. {s.get('narration')}" for s in scenes)
        return (
            f"현재 대본:\n{summary}\n\n수정 예: `훅: 새 문장` / `장면 2: 새 나레이션`",
            None,
        )

    return (
        "예시:\n• `훅: 새로운 한 줄`\n• `장면 2: 바꿀 나레이션`\n• `대본 보여줘`",
        None,
    )


async def chat_edit_script(
    settings: Settings,
    job: Job,
    message: str,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    if not job.script or not job.script.content:
        return {
            "reply": "대본이 없습니다. Run을 먼저 실행하세요.",
            "script": None,
            "applied": False,
        }

    script = job.script.content
    reference_ctx = _load_reference_context(job, settings)

    if settings.openai_api_key:
        result = await _openai_chat_edit(settings, script, message, history or [], reference_ctx)
        if result:
            return result

    reply, updated = _rule_based_chat(script, message)
    return {"reply": reply, "script": updated, "applied": updated is not None}


def _load_reference_context(job: Job, settings: Settings) -> dict[str, Any] | None:
    job_dir = Path(settings.data_dir) / "jobs" / job.code
    ref_path = job_dir / "reference_analysis.json"
    if ref_path.exists():
        return json.loads(ref_path.read_text(encoding="utf-8"))
    if job.topic_candidate and job.topic_candidate.score_breakdown:
        b = job.topic_candidate.score_breakdown
        if b.get("reference_url"):
            return {
                "url": b.get("reference_url"),
                "title": b.get("reference_title"),
                **(b.get("reference_analysis") or {}),
            }
    return None


async def _openai_chat_edit(
    settings: Settings,
    script: dict,
    message: str,
    history: list[dict[str, str]],
    reference_ctx: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    ref_note = ""
    if reference_ctx:
        ref_note = (
            f"\nReference Shorts (inspiration only, do not copy verbatim): "
            f"{json.dumps(reference_ctx, ensure_ascii=False)}"
        )
    system = (
        "Korean YouTube Shorts script editor. Apply user edits to script JSON. "
        "Keep the video original — inspired by reference structure only."
        f"{ref_note} "
        "Respond JSON: {reply: string, script: object|null}."
    )
    messages = [{"role": "system", "content": system}]
    for h in history[-6:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append(
        {
            "role": "user",
            "content": f"Script:\n{json.dumps(script, ensure_ascii=False)}\n\nEdit: {message}",
        }
    )
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.4},
            )
            if resp.status_code != 200:
                return None
            content = resp.json()["choices"][0]["message"]["content"]
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(content[start:end])
                return {
                    "reply": parsed.get("reply", content),
                    "script": parsed.get("script"),
                    "applied": parsed.get("script") is not None,
                }
            return {"reply": content, "script": None, "applied": False}
    except Exception:
        return None
