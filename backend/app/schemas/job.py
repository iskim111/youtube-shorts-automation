from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class JobStageResponse(BaseModel):
    stage: str
    status: str
    output_uri: str | None = None


class JobSummaryResponse(BaseModel):
    id: str
    channel_name: str
    status: str
    topic_score: float
    hook_line: str


class JobDetailResponse(BaseModel):
    id: str
    channel_name: str
    status: str
    operation_mode: Literal["manual", "semi_auto", "auto"]
    topic_score: float
    hook_line: str
    stages: list[JobStageResponse]
    hold_reason: str | None
    script: dict[str, Any] | None = None
    youtube_video_id: str | None = None
    upload_dry_run: bool | None = None
    metadata_title: str | None = None
    render_template: str = "bold_center"
    scheduled_publish_at: datetime | None = None
    assets: list[dict[str, Any]] = Field(default_factory=list)


class JobScheduleRequest(BaseModel):
    scheduled_publish_at: datetime
    render_template: str | None = None


class PipelineRunResponse(BaseModel):
    job_id: str
    status: str
    message: str


class PublishResponse(BaseModel):
    job_id: str
    status: str
    youtube_video_id: str | None
    dry_run: bool
    title: str
    privacy_status: str


class JobPreviewResponse(BaseModel):
    job_id: str
    status: str
    hook_line: str
    script: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    reference: dict[str, Any] | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    youtube_video_id: str | None = None


class JobChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = Field(default_factory=list)


class JobChatResponse(BaseModel):
    reply: str
    script: dict[str, Any] | None = None
    applied: bool = False


class JobScriptUpdateRequest(BaseModel):
    script: dict[str, Any]
