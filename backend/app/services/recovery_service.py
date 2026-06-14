"""장애 복구 — 기술 오류 재시도."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.enums import JobStatus, StageStatus
from app.models.job import Job
from app.services.audit_service import log_action
from app.services.notification_service import notify
from app.services.pipeline_service import PipelineError, load_job_full, run_pipeline_to_qa
from app.services.upload_service import publish_job

MAX_RETRIES = 5
RETRYABLE_STATUSES = {JobStatus.UPLOAD_FAILED}
RETRYABLE_STAGES = {StageStatus.FAILED}


async def retry_job(session: AsyncSession, job: Job, settings: Settings) -> dict:
    if job.retry_count >= MAX_RETRIES:
        raise PipelineError(f"최대 재시도({MAX_RETRIES}) 초과")

    job.retry_count += 1
    failed_stage = next((s for s in job.stages if s.status == StageStatus.FAILED), None)

    if job.status == JobStatus.UPLOAD_FAILED:
        job.status = JobStatus.QA_APPROVED
        result = await publish_job(session, job, settings)
        action = "retry_upload"
    elif failed_stage and failed_stage.stage in ("render", "asset", "tts"):
        for s in job.stages:
            if s.status == StageStatus.FAILED:
                s.status = StageStatus.PENDING
                s.error_message = None
        job.status = JobStatus.TOPIC_APPROVED
        await run_pipeline_to_qa(session, job, settings)
        result = {"status": job.status.value}
        action = "retry_pipeline"
    elif job.status in (JobStatus.RIGHTS_HOLD, JobStatus.QA_HOLD):
        raise PipelineError("정책/권리 보류는 재시도 불가 — Rights Center에서 검수")
    else:
        raise PipelineError(f"재시도 불가 상태: {job.status.value}")

    await log_action(session, action, "job", job.code, {"retry_count": job.retry_count, **result})
    await notify(settings, "pipeline.failed", f"재시도 {job.retry_count}회 성공", job_id=job.code)
    return {"job_id": job.code, "retry_count": job.retry_count, **result}


async def retry_job_by_code(session: AsyncSession, job_code: str, settings: Settings) -> dict:
    job = await load_job_full(session, job_code)
    if not job:
        raise PipelineError("작업을 찾을 수 없습니다.")
    return await retry_job(session, job, settings)
