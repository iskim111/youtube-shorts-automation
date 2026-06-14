from typing import Literal

from pydantic import BaseModel


class ChannelResponse(BaseModel):
    id: str
    name: str
    operation_mode: Literal["manual", "semi_auto", "auto"]
    daily_upload_cap: int
    category_allowlist: list[str]
    is_active: bool
    youtube_channel_id: str | None = None
    oauth_connected: bool = False
    youtube_channel_title: str | None = None
