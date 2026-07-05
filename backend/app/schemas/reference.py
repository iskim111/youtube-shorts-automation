import uuid

from pydantic import BaseModel, Field


class ReferenceAnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=10, description="YouTube Shorts URL")
    channel_id: uuid.UUID


class ReferenceScenePreview(BaseModel):
    seq: int
    narration: str
    visual_hint: str | None = None
    duration_sec: int | None = None


class ReferenceAnalyzeResponse(BaseModel):
    video_id: str
    url: str
    title: str
    author_name: str | None = None
    thumbnail_url: str | None = None
    category: str
    hook_line: str
    keyword_cluster: list[str]
    style_notes: str = ""
    script: dict


class ReferenceCreateJobRequest(BaseModel):
    url: str = Field(..., min_length=10)
    channel_id: uuid.UUID
    analysis: dict | None = None


class ReferenceCreateJobResponse(BaseModel):
    topic_id: str
    job_id: str
    status: str
    hook_line: str
    reference_url: str
    reference_title: str
