"""Auto mode — low-risk allowlist만 자동 게시."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.enums import CopyrightRisk, JobStatus, OperationMode, TopicStatus
from app.models.job import Job
from app.services.audit_service import log_action
from app.services.notification_service import notify
from app.services.quota_manager import can_upload, record_upload
from app.services.upload_service import publish_job

AUTO_ALLOWED_CATEGORIES = {"comedy", "food", "daily_pet", "tips"}


def is_auto_eligible(job: Job) -> bool:
    if job.channel.operation_mode != OperationMode.AUTO:
        return False
    topic = job.topic_candidate
    if not topic:
        return False
    if topic.copyright_risk != CopyrightRisk.LOW:
        return False
    if topic.category not in AUTO_ALLOWED_CATEGORIES:
        return False
    if topic.status != TopicStatus.APPROVED:
        return False
    if job.status != JobStatus.QA_PENDING:
        return False
    return True


async def try_auto_publish(session: AsyncSession, job: Job, settings: Settings) -> dict | None:
    if not is_auto_eligible(job):
        return None

    ok, reason = await can_upload(settings)
    if not ok:
        await notify(settings, "auto.publish", f"자동 게시 스킵: {reason}", job_id=job.code)
        return None

    try:
        result = await publish_job(session, job, settings)
        await record_upload(settings)
        await log_action(session, "auto_publish", "job", job.code, result)
        await notify(settings, "auto.publish", "자동 게시 완료", **result)
        return result
    except Exception as exc:
        await notify(settings, "upload.failed", str(exc), job_id=job.code)
        return None
