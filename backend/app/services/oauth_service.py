import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import Settings
from app.integrations.youtube_api import fetch_my_channel
from app.integrations.youtube_oauth import exchange_code_for_tokens
from app.models.channel import Channel
from app.models.oauth_credential import OAuthCredential


async def get_channel_with_oauth(session: AsyncSession, channel_id: uuid.UUID) -> Channel | None:
    result = await session.execute(
        select(Channel)
        .options(selectinload(Channel.oauth_credential))
        .where(Channel.id == channel_id)
    )
    return result.scalar_one_or_none()


async def save_oauth_tokens(
    session: AsyncSession,
    settings: Settings,
    channel_id: uuid.UUID,
    token_data: dict,
) -> OAuthCredential:
    channel = await get_channel_with_oauth(session, channel_id)
    if not channel:
        raise ValueError("채널을 찾을 수 없습니다.")

    record = channel.oauth_credential
    if record is None:
        record = OAuthCredential(channel_id=channel_id, access_token=token_data["access_token"])
        session.add(record)

    record.access_token = token_data["access_token"]
    record.refresh_token = token_data.get("refresh_token") or record.refresh_token
    record.token_expires_at = token_data.get("token_expires_at")
    record.scopes = token_data.get("scopes", settings.youtube_scope_list)

    await session.flush()

    channel_info = await fetch_my_channel(settings, record)
    record.youtube_channel_id = channel_info["youtube_channel_id"]
    record.youtube_channel_title = channel_info["youtube_channel_title"]
    channel.youtube_channel_id = channel_info["youtube_channel_id"]

    await session.flush()
    return record


async def disconnect_oauth(session: AsyncSession, channel_id: uuid.UUID) -> None:
    channel = await get_channel_with_oauth(session, channel_id)
    if not channel:
        raise ValueError("채널을 찾을 수 없습니다.")
    if channel.oauth_credential:
        await session.delete(channel.oauth_credential)
    channel.youtube_channel_id = None
    await session.flush()
