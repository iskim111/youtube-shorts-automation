import uuid

from pydantic import BaseModel, Field


class CharacterCreateRequest(BaseModel):
    name: str
    role: str
    heygen_avatar_id: str = ""
    elevenlabs_voice_id: str = ""
    speech_style: str = ""
    language_primary: str = "ko"
    avatar_image_url: str | None = None


class CharacterUpdateRequest(BaseModel):
    name: str | None = None
    role: str | None = None
    heygen_avatar_id: str | None = None
    elevenlabs_voice_id: str | None = None
    speech_style: str | None = None
    language_primary: str | None = None
    avatar_image_url: str | None = None
    is_active: bool | None = None


class CharacterResponse(BaseModel):
    id: str
    code: str
    name: str
    role: str
    heygen_avatar_id: str
    elevenlabs_voice_id: str
    speech_style: str
    language_primary: str
    avatar_image_url: str | None
    is_active: bool
    sort_order: int


class SeriesPresetResponse(BaseModel):
    id: str
    label: str
    roles: list[str]


class SeriesEpisodeRequest(BaseModel):
    channel_id: uuid.UUID
    preset: str = "grandma_youth_en"
    topic_hint: str = ""


class TrendingCreateRequest(BaseModel):
    channel_id: uuid.UUID


class ProductionCreateResponse(BaseModel):
    topic_id: str
    job_id: str
    status: str
    hook_line: str
    script_format: str = "monologue"
