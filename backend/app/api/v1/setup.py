from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_effective_settings_dep
from app.config import Settings
from app.models.channel import Channel
from app.services.ffmpeg_path import ffmpeg_available, ffmpeg_version, resolve_ffmpeg
from app.services.quota_manager import get_quota_status

router = APIRouter()


@router.get("/status")
async def setup_status(db: AsyncSession = Depends(get_db), settings: Settings = Depends(get_effective_settings_dep)):
    result = await db.execute(
        select(Channel).options(selectinload(Channel.oauth_credential)).where(Channel.is_active.is_(True))
    )
    channels = result.scalars().all()
    oauth_connected = any(c.oauth_credential for c in channels)

    checks = [
        {
            "id": "ffmpeg",
            "label": "FFmpeg",
            "ok": ffmpeg_available(),
            "detail": ffmpeg_version() or "미설치 — scripts/install-ffmpeg.ps1 실행",
            "path": resolve_ffmpeg(),
        },
        {
            "id": "youtube_oauth",
            "label": "YouTube OAuth 설정",
            "ok": settings.youtube_configured,
            "detail": "YOUTUBE_CLIENT_ID/SECRET 설정됨" if settings.youtube_configured else ".env에 OAuth 키 필요",
        },
        {
            "id": "youtube_connected",
            "label": "YouTube 채널 연결",
            "ok": oauth_connected,
            "detail": "Settings에서 OAuth 연결" if not oauth_connected else "연결됨",
        },
        {
            "id": "dry_run",
            "label": "Dry-run 업로드",
            "ok": True,
            "detail": "활성" if settings.pilot_dry_run_upload else "비활성 — 실제 업로드 모드",
            "warning": not settings.pilot_dry_run_upload,
        },
        {
            "id": "openai",
            "label": "OpenAI",
            "ok": bool(settings.openai_api_key),
            "detail": "시나리오·채팅·주제 변형" if settings.openai_api_key else "Settings에서 키 입력",
        },
        {
            "id": "youtube_data",
            "label": "YouTube Data API",
            "ok": settings.youtube_data_configured,
            "detail": "TOP 100 수집" if settings.youtube_data_configured else "YOUTUBE_API_KEY 필요",
        },
        {
            "id": "elevenlabs",
            "label": "ElevenLabs TTS",
            "ok": settings.elevenlabs_configured,
            "detail": "캐릭터 음성" if settings.elevenlabs_configured else "선택·권장",
        },
        {
            "id": "heygen",
            "label": "HeyGen AI 영상",
            "ok": settings.heygen_configured,
            "detail": "AI 캐릭터 영상" if settings.heygen_configured else "HEYGEN_API_KEY 필요",
        },
        {
            "id": "stock_api",
            "label": "스톡 API (Pexels/Pixabay)",
            "ok": settings.stock_configured,
            "detail": "설정됨" if settings.stock_configured else "선택 — 없으면 플레이스홀더 렌더",
        },
        {
            "id": "asset_strategy",
            "label": "에셋 전략",
            "ok": True,
            "detail": (
                f"{settings.asset_strategy}"
                + (" + AI 이미지" if settings.ai_image_configured else "")
                + (" + AI 영상" if settings.ai_video_configured else "")
            ),
        },
    ]

    ready_for_real_upload = (
        ffmpeg_available()
        and settings.youtube_configured
        and oauth_connected
        and not settings.pilot_dry_run_upload
    )

    quota = await get_quota_status(settings)

    return {
        "ready_for_real_upload": ready_for_real_upload,
        "checks": checks,
        "quota": quota,
        "redirect_uri": settings.youtube_redirect_uri,
        "asset_strategy": settings.asset_strategy,
        "ai_image_configured": settings.ai_image_configured,
        "ai_video_configured": settings.ai_video_configured,
    }
