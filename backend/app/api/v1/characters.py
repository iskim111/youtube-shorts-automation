from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.api.deps import get_db
from app.schemas.character import (
    CharacterCreateRequest,
    CharacterResponse,
    CharacterUpdateRequest,
    SeriesEpisodeRequest,
    SeriesPresetResponse,
    ProductionCreateResponse,
)
from app.services.character_service import ensure_default_characters, list_characters, next_character_code
from app.services.production_service import create_series_episode
from app.services.scenario_generator import SERIES_PRESETS
from app.services.settings_store import get_effective_settings
from app.models.character import Character

router = APIRouter()


def _char_response(c: Character) -> CharacterResponse:
    return CharacterResponse(
        id=str(c.id),
        code=c.code,
        name=c.name,
        role=c.role,
        heygen_avatar_id=c.heygen_avatar_id,
        elevenlabs_voice_id=c.elevenlabs_voice_id,
        speech_style=c.speech_style,
        language_primary=c.language_primary,
        avatar_image_url=c.avatar_image_url,
        is_active=c.is_active,
        sort_order=c.sort_order,
    )


@router.get("/presets", response_model=list[SeriesPresetResponse])
async def list_series_presets():
    return [
        SeriesPresetResponse(id=k, label=v["label"], roles=v["roles"])
        for k, v in SERIES_PRESETS.items()
    ]


@router.get("", response_model=list[CharacterResponse])
async def get_characters(db: AsyncSession = Depends(get_db)):
    await ensure_default_characters(db)
    await db.commit()
    chars = await list_characters(db, active_only=False)
    return [_char_response(c) for c in chars]


@router.post("", response_model=CharacterResponse)
async def create_character(body: CharacterCreateRequest, db: AsyncSession = Depends(get_db)):
    code = await next_character_code(db)
    char = Character(code=code, **body.model_dump())
    db.add(char)
    await db.commit()
    await db.refresh(char)
    return _char_response(char)


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    body: CharacterUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Character).where(Character.code == character_id))
    char = result.scalar_one_or_none()
    if not char:
        try:
            from uuid import UUID

            result = await db.execute(select(Character).where(Character.id == UUID(character_id)))
            char = result.scalar_one_or_none()
        except Exception:
            char = None
    if not char:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(char, field, value)
    await db.commit()
    await db.refresh(char)
    return _char_response(char)


@router.post("/series/episode", response_model=ProductionCreateResponse)
async def create_episode(body: SeriesEpisodeRequest, db: AsyncSession = Depends(get_db)):
    from app.models.channel import Channel

    settings = await get_effective_settings(db)
    channel = await db.get(Channel, body.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
    await ensure_default_characters(db)
    try:
        topic, job, script, _ = await create_series_episode(
            db,
            settings,
            channel=channel,
            preset=body.preset,
            topic_hint=body.topic_hint,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    return ProductionCreateResponse(
        topic_id=topic.code,
        job_id=job.code,
        status=job.status.value,
        hook_line=topic.hook_line,
        script_format=script.get("format", "dialogue"),
    )
