"""Resolved visual assets for render pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

MediaKind = Literal["video", "image", "placeholder"]


@dataclass
class ResolvedAsset:
    source_type: str
    storage_uri: str | None
    source_url: str | None = None
    license_status: str = "low"
    media_kind: MediaKind = "video"
    scene_seq: int = 1
    duration_sec: int = 8
    provider: str = "unknown"
    metadata: dict = field(default_factory=dict)
