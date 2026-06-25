"""AI video providers (Runway, Luma 등) — 확장용 스텁."""

from __future__ import annotations

from pathlib import Path

from app.config import Settings


async def generate_scene_video(
    settings: Settings,
    prompt: str,
    dest: Path,
    *,
    duration_sec: int = 5,
) -> bool:
    """유료 AI 영상 API 연동 지점. 키·provider 설정 시 구현 확장."""
    if not settings.ai_video_configured:
        return False

    provider = settings.ai_video_provider
    if provider == "runway" and settings.runway_api_key:
        # TODO: Runway Gen-3 API (async job poll)
        return False
    if provider == "luma" and settings.luma_api_key:
        # TODO: Luma Dream Machine API
        return False
    return False
