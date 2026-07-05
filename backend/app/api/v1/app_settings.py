from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.app_settings import ApiKeysResponse, ApiKeysUpdateRequest
from app.services.settings_store import (
    get_effective_settings,
    mask_secret,
    save_settings,
    settings_status,
)

router = APIRouter()


def _to_response(settings) -> ApiKeysResponse:
    return ApiKeysResponse(
        openai_api_key=mask_secret(settings.openai_api_key),
        youtube_api_key=mask_secret(getattr(settings, "youtube_api_key", "")),
        elevenlabs_api_key=mask_secret(getattr(settings, "elevenlabs_api_key", "")),
        heygen_api_key=mask_secret(getattr(settings, "heygen_api_key", "")),
        pexels_api_key=mask_secret(settings.pexels_api_key),
        pixabay_api_key=mask_secret(settings.pixabay_api_key),
        youtube_client_id=mask_secret(settings.youtube_client_id),
        youtube_client_secret=mask_secret(settings.youtube_client_secret),
        video_mode=getattr(settings, "video_mode", "ai_character"),
        configured=settings_status(settings),
    )


@router.get("/keys", response_model=ApiKeysResponse)
async def get_api_keys(db: AsyncSession = Depends(get_db)):
    settings = await get_effective_settings(db)
    return _to_response(settings)


@router.put("/keys", response_model=ApiKeysResponse)
async def update_api_keys(body: ApiKeysUpdateRequest, db: AsyncSession = Depends(get_db)):
    await save_settings(db, body.model_dump())
    await db.commit()
    settings = await get_effective_settings(db)
    return _to_response(settings)
