from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.job import Job

router = APIRouter()


class CalendarSlot(BaseModel):
    job_id: str
    channel_name: str
    hook_line: str
    status: str
    scheduled_publish_at: datetime | None
    youtube_video_id: str | None = None
    priority: int


@router.get("", response_model=list[CalendarSlot])
async def upload_calendar(
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Job)
        .options(
            selectinload(Job.topic_candidate),
            selectinload(Job.channel),
            selectinload(Job.upload_record),
        )
        .where(Job.scheduled_publish_at.isnot(None))
        .order_by(Job.scheduled_publish_at.asc())
    )
    jobs = result.scalars().all()

    slots = []
    for job in jobs:
        topic = job.topic_candidate
        upload = job.upload_record
        slots.append(
            CalendarSlot(
                job_id=job.code,
                channel_name=job.channel.name if job.channel else "",
                hook_line=topic.hook_line if topic else "",
                status=job.status.value,
                scheduled_publish_at=job.scheduled_publish_at,
                youtube_video_id=upload.youtube_video_id if upload else None,
                priority=job.priority,
            )
        )
    return slots
