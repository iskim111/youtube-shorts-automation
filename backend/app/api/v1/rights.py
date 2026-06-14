from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.enums import JobStatus, TopicStatus
from app.models.job import Job
from app.models.topic_candidate import TopicCandidate
from app.schemas.mappers import job_to_summary

router = APIRouter()


class RightsReviewRequest(BaseModel):
    action: str  # approve | reject
    note: str | None = None


class RightsQueueItem(BaseModel):
    job_id: str | None
    topic_id: str | None
    hook_line: str
    channel_name: str
    status: str
    hold_reason: str | None
    copyright_risk: str | None
    category: str | None


@router.get("/queue", response_model=list[RightsQueueItem])
async def rights_queue(db: AsyncSession = Depends(get_db)):
    items: list[RightsQueueItem] = []

    job_result = await db.execute(
        select(Job)
        .options(selectinload(Job.topic_candidate), selectinload(Job.channel))
        .where(Job.status.in_([JobStatus.RIGHTS_HOLD, JobStatus.QA_HOLD]))
    )
    for job in job_result.scalars().all():
        topic = job.topic_candidate
        items.append(
            RightsQueueItem(
                job_id=job.code,
                topic_id=topic.code if topic else None,
                hook_line=topic.hook_line if topic else "",
                channel_name=job.channel.name if job.channel else "",
                status=job.status.value,
                hold_reason=job.hold_reason,
                copyright_risk=topic.copyright_risk.value if topic else None,
                category=topic.category if topic else None,
            )
        )

    topic_result = await db.execute(
        select(TopicCandidate).where(
            TopicCandidate.status.in_([TopicStatus.REVIEW_REQUIRED, TopicStatus.ON_HOLD])
        )
    )
    for topic in topic_result.scalars().all():
        items.append(
            RightsQueueItem(
                job_id=None,
                topic_id=topic.code,
                hook_line=topic.hook_line,
                channel_name="",
                status=topic.status.value,
                hold_reason=f"copyright:{topic.copyright_risk.value}",
                copyright_risk=topic.copyright_risk.value,
                category=topic.category,
            )
        )

    return items


@router.post("/jobs/{job_id}/review")
async def review_job(job_id: str, body: RightsReviewRequest, db: AsyncSession = Depends(get_db)):
    from app.services.pipeline_service import load_job_full

    job = await load_job_full(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    if body.action == "approve":
        if job.status == JobStatus.RIGHTS_HOLD:
            job.status = JobStatus.RIGHTS_PASSED
        elif job.status == JobStatus.QA_HOLD:
            job.status = JobStatus.QA_PENDING
        job.hold_reason = None
    elif body.action == "reject":
        job.status = JobStatus.CANCELLED
        job.hold_reason = body.note or "운영자 거부"
    else:
        raise HTTPException(status_code=400, detail="action은 approve 또는 reject")

    await db.commit()
    return {"job_id": job.code, "status": job.status.value}
