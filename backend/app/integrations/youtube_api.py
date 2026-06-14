"""YouTube Data API v3 wrapper."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from functools import partial
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.config import Settings
from app.models.oauth_credential import OAuthCredential


class YouTubeAPIError(Exception):
    pass


def _to_credentials(settings: Settings, record: OAuthCredential) -> Credentials:
    expiry = record.token_expires_at
    if expiry and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=UTC)
    return Credentials(
        token=record.access_token,
        refresh_token=record.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.youtube_client_id,
        client_secret=settings.youtube_client_secret,
        scopes=record.scopes,
        expiry=expiry,
    )


def _refresh_if_needed_sync(settings: Settings, record: OAuthCredential) -> Credentials:
    creds = _to_credentials(settings, record)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds.valid and creds.refresh_token:
        creds.refresh(Request())
    return creds


async def refresh_credentials_if_needed(
    settings: Settings, record: OAuthCredential
) -> Credentials:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_refresh_if_needed_sync, settings, record))


def apply_refreshed_tokens(record: OAuthCredential, creds: Credentials) -> None:
    record.access_token = creds.token
    if creds.refresh_token:
        record.refresh_token = creds.refresh_token
    if creds.expiry:
        record.token_expires_at = creds.expiry.replace(tzinfo=UTC)
    else:
        record.token_expires_at = datetime.now(UTC) + timedelta(hours=1)
    record.last_refreshed_at = datetime.now(UTC)


def _fetch_my_channel_sync(creds: Credentials) -> dict[str, str]:
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    response = youtube.channels().list(part="snippet", mine=True).execute()
    items = response.get("items", [])
    if not items:
        raise YouTubeAPIError("연결된 YouTube 채널을 찾을 수 없습니다.")
    channel = items[0]
    return {
        "youtube_channel_id": channel["id"],
        "youtube_channel_title": channel["snippet"]["title"],
    }


async def fetch_my_channel(settings: Settings, record: OAuthCredential) -> dict[str, str]:
    creds = await refresh_credentials_if_needed(settings, record)
    apply_refreshed_tokens(record, creds)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_fetch_my_channel_sync, creds))


def _upload_video_sync(
    creds: Credentials,
    file_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str = "private",
    publish_at: datetime | None = None,
) -> str:
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    body: dict[str, Any] = {
        "snippet": {"title": title, "description": description, "tags": tags},
        "status": {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": False},
    }
    if publish_at:
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    media = MediaFileUpload(file_path, chunksize=1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pass
    return response["id"]


async def upload_video(
    settings: Settings,
    record: OAuthCredential,
    file_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str = "private",
    publish_at: datetime | None = None,
) -> str:
    creds = await refresh_credentials_if_needed(settings, record)
    apply_refreshed_tokens(record, creds)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        partial(
            _upload_video_sync,
            creds,
            file_path,
            title,
            description,
            tags,
            privacy_status,
            publish_at,
        ),
    )
