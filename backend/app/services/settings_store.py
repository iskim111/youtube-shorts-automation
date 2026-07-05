"""DB + .env 병합 설정. UI에서 저장한 API 키를 런타임에 반영."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.app_setting import AppSetting

SETTING_KEYS = (
    "openai_api_key",
    "youtube_api_key",
    "elevenlabs_api_key",
    "heygen_api_key",
    "pexels_api_key",
    "pixabay_api_key",
    "youtube_client_id",
    "youtube_client_secret",
    "video_mode",
)

MASK = "••••••••"


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return MASK
    return value[:4] + MASK + value[-4:]


async def load_overrides(session: AsyncSession) -> dict[str, str]:
    result = await session.execute(select(AppSetting).where(AppSetting.key.in_(SETTING_KEYS)))
    return {row.key: row.value for row in result.scalars().all() if row.value}


def apply_overrides(base: Settings, overrides: dict[str, str]) -> Settings:
    if not overrides:
        return base
    patch: dict = {}
    for key in SETTING_KEYS:
        val = overrides.get(key)
        if val:
            patch[key] = val
    if not patch:
        return base
    return base.model_copy(update=patch)


async def get_effective_settings(session: AsyncSession) -> Settings:
    overrides = await load_overrides(session)
    return apply_overrides(get_settings(), overrides)


async def save_settings(session: AsyncSession, updates: dict[str, str]) -> None:
    for key, value in updates.items():
        if key not in SETTING_KEYS:
            continue
        if value == "" or value == MASK or MASK in value:
            continue
        existing = await session.get(AppSetting, key)
        if existing:
            existing.value = value
        else:
            session.add(AppSetting(key=key, value=value))
    await session.flush()


def settings_status(settings: Settings) -> dict[str, bool]:
    return {
        "openai": bool(settings.openai_api_key),
        "youtube_data": bool(getattr(settings, "youtube_api_key", "")),
        "elevenlabs": bool(getattr(settings, "elevenlabs_api_key", "")),
        "heygen": bool(getattr(settings, "heygen_api_key", "")),
        "stock": bool(settings.pexels_api_key or settings.pixabay_api_key),
        "youtube_oauth": settings.youtube_configured,
    }
