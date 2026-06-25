import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.config import Settings, get_settings
from app.integrations.youtube_oauth import (
    build_authorization_url,
    decode_oauth_state,
    exchange_code_for_tokens,
)
from app.models.channel import Channel
from app.models.enums import OperationMode
from app.schemas.channel import ChannelResponse
from app.schemas.mappers import channel_to_response
from app.schemas.oauth import OAuthCallbackResult, OAuthStartResponse, OAuthStatusResponse
from app.services.oauth_service import disconnect_oauth, get_channel_with_oauth, save_oauth_tokens

router = APIRouter()


class ChannelCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    operation_mode: OperationMode = OperationMode.SEMI_AUTO
    daily_upload_cap: int = Field(default=5, ge=1, le=100)
    category_allowlist: list[str] = Field(default_factory=lambda: ["comedy", "food", "daily_pet", "tips"])


@router.post("", response_model=ChannelResponse)
async def create_channel(body: ChannelCreateRequest, db: AsyncSession = Depends(get_db)):
    channel = Channel(
        name=body.name,
        operation_mode=body.operation_mode,
        daily_upload_cap=body.daily_upload_cap,
        category_allowlist=body.category_allowlist,
        is_active=True,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel_to_response(channel)


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not settings.youtube_configured:
        raise HTTPException(status_code=503, detail="YouTube OAuth가 설정되지 않았습니다.")

    try:
        channel_id, code_verifier = decode_oauth_state(settings, state)
        token_data = exchange_code_for_tokens(settings, code, code_verifier=code_verifier)
        record = await save_oauth_tokens(db, settings, channel_id, token_data)
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=502, detail=f"OAuth 토큰 교환 실패: {exc}") from exc

    title = quote(record.youtube_channel_title or "")
    redirect_url = (
        f"{settings.frontend_base_url}/settings"
        f"?oauth=success&channel_id={channel_id}&youtube_channel_title={title}"
    )
    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("", response_model=list[ChannelResponse])
async def list_channels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Channel)
        .options(selectinload(Channel.oauth_credential))
        .where(Channel.is_active.is_(True))
    )
    channels = result.scalars().all()
    return [channel_to_response(c) for c in channels]


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    channel = await get_channel_with_oauth(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
    return channel_to_response(channel)


@router.post("/{channel_id}/oauth/start", response_model=OAuthStartResponse)
async def start_oauth(
    channel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not settings.youtube_configured:
        raise HTTPException(
            status_code=503,
            detail="YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET 환경변수를 설정하세요.",
        )

    channel = await db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")

    authorization_url, state = build_authorization_url(settings, channel_id)
    return OAuthStartResponse(authorization_url=authorization_url, state=state)


@router.get("/{channel_id}/oauth/status", response_model=OAuthStatusResponse)
async def oauth_status(channel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    channel = await get_channel_with_oauth(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")

    oauth = channel.oauth_credential
    if not oauth:
        return OAuthStatusResponse(connected=False)

    return OAuthStatusResponse(
        connected=True,
        youtube_channel_id=oauth.youtube_channel_id,
        youtube_channel_title=oauth.youtube_channel_title,
        scopes=oauth.scopes or [],
        token_expires_at=oauth.token_expires_at.isoformat() if oauth.token_expires_at else None,
        last_refreshed_at=oauth.last_refreshed_at.isoformat() if oauth.last_refreshed_at else None,
    )


@router.delete("/{channel_id}/oauth", response_model=OAuthCallbackResult)
async def revoke_oauth(channel_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        await disconnect_oauth(db, channel_id)
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return OAuthCallbackResult(
        success=True,
        channel_id=str(channel_id),
        message="YouTube 연결이 해제되었습니다.",
    )
