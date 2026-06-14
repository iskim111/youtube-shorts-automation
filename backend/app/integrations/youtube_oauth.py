"""Google OAuth 2.0 helpers for YouTube channel connection."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from google_auth_oauthlib.flow import Flow
from jose import JWTError, jwt

from app.config import Settings

STATE_ALGORITHM = "HS256"
STATE_EXPIRE_MINUTES = 15


def _client_config(settings: Settings) -> dict[str, Any]:
    return {
        "web": {
            "client_id": settings.youtube_client_id,
            "client_secret": settings.youtube_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.youtube_redirect_uri],
        }
    }


def create_oauth_flow(settings: Settings) -> Flow:
    return Flow.from_client_config(
        _client_config(settings),
        scopes=settings.youtube_scope_list,
        redirect_uri=settings.youtube_redirect_uri,
    )


def build_authorization_url(settings: Settings, channel_id: uuid.UUID) -> tuple[str, str]:
    flow = create_oauth_flow(settings)
    state = _encode_state(settings, channel_id)
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return authorization_url, state


def exchange_code_for_tokens(settings: Settings, code: str) -> dict[str, Any]:
    flow = create_oauth_flow(settings)
    flow.fetch_token(code=code)
    credentials = flow.credentials
    expires_at = None
    if credentials.expiry:
        expires_at = credentials.expiry.replace(tzinfo=UTC)
    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_expires_at": expires_at,
        "scopes": list(credentials.scopes or settings.youtube_scope_list),
    }


def _encode_state(settings: Settings, channel_id: uuid.UUID) -> str:
    payload = {
        "channel_id": str(channel_id),
        "exp": datetime.now(UTC) + timedelta(minutes=STATE_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=STATE_ALGORITHM)


def decode_state(settings: Settings, state: str) -> uuid.UUID:
    try:
        payload = jwt.decode(state, settings.jwt_secret, algorithms=[STATE_ALGORITHM])
        return uuid.UUID(payload["channel_id"])
    except (JWTError, KeyError, ValueError) as exc:
        raise ValueError("유효하지 않은 OAuth state입니다.") from exc
