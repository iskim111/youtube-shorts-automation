import uuid
from typing import Literal

from pydantic import BaseModel, Field


class TopicScores(BaseModel):
    view_potential: float
    competition: float
    production: float
    copyright_safety: float
    final: float


class TopicCandidateResponse(BaseModel):
    id: str
    category: str
    keyword_cluster: list[str]
    hook_line: str
    scores: TopicScores
    copyright_risk: Literal["low", "medium", "high"]
    ai_label_required: bool
    status: str


class TopicGenerateRequest(BaseModel):
    channel_id: uuid.UUID
    limit: int = Field(default=5, ge=1, le=20)
