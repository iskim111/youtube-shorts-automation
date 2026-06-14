from pydantic import BaseModel


class OAuthStartResponse(BaseModel):
    authorization_url: str
    state: str


class OAuthStatusResponse(BaseModel):
    connected: bool
    youtube_channel_id: str | None = None
    youtube_channel_title: str | None = None
    scopes: list[str] = []
    token_expires_at: str | None = None
    last_refreshed_at: str | None = None


class OAuthCallbackResult(BaseModel):
    success: bool
    channel_id: str
    youtube_channel_id: str | None = None
    youtube_channel_title: str | None = None
    message: str
