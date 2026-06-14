from __future__ import annotations

from datetime import UTC, datetime

from app.models.enums import StageStatus
from app.models.job import Job


class PipelineError(Exception):
    def __init__(self, message: str, stage: str | None = None):
        super().__init__(message)
        self.stage = stage


def get_stage(job: Job, name: str):
    for s in job.stages:
        if s.stage == name:
            return s
    raise PipelineError(f"스테이지 없음: {name}")


def start_stage(stage) -> None:
    stage.status = StageStatus.PROCESSING
    stage.started_at = datetime.now(UTC)
    stage.progress = 10


def finish_stage(stage, output_uri: str | None = None) -> None:
    stage.status = StageStatus.SUCCESS
    stage.finished_at = datetime.now(UTC)
    stage.progress = 100
    if output_uri:
        stage.output_uri = output_uri


def fail_stage(stage, message: str) -> None:
    stage.status = StageStatus.FAILED
    stage.finished_at = datetime.now(UTC)
    stage.error_message = message
