from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import JobStatus, OperationMode, StageStatus, TopicStatus
from app.models.job import Job
from app.models.job_stage import DEFAULT_STAGES, JobStage
from app.models.topic_candidate import TopicCandidate


async def next_job_code(session: AsyncSession) -> str:
    result = await session.execute(select(func.count()).select_from(Job))
    count = result.scalar() or 0
    return f"J-{count + 1:04d}"


async def create_job_from_topic(
    session: AsyncSession,
    topic: TopicCandidate,
    operation_mode: OperationMode,
) -> Job:
    if topic.status == TopicStatus.APPROVED:
        raise ValueError("이미 승인된 주제입니다.")
    if topic.status in (TopicStatus.REJECTED, TopicStatus.ON_HOLD):
        raise ValueError(f"승인할 수 없는 상태입니다: {topic.status.value}")

    job_code = await next_job_code(session)
    job = Job(
        code=job_code,
        channel_id=topic.channel_id,
        topic_candidate_id=topic.id,
        status=JobStatus.TOPIC_APPROVED,
        operation_mode=operation_mode,
    )
    session.add(job)
    await session.flush()

    for stage_name in DEFAULT_STAGES:
        session.add(JobStage(job_id=job.id, stage=stage_name, status=StageStatus.PENDING))

    topic.status = TopicStatus.APPROVED
    await session.flush()
    return job


async def get_topic_by_code(session: AsyncSession, code: str) -> TopicCandidate | None:
    result = await session.execute(select(TopicCandidate).where(TopicCandidate.code == code))
    return result.scalar_one_or_none()


async def get_job_by_code(session: AsyncSession, code: str) -> Job | None:
    result = await session.execute(
        select(Job)
        .options(
            selectinload(Job.stages),
            selectinload(Job.topic_candidate),
            selectinload(Job.channel),
        )
        .where(Job.code == code)
    )
    return result.scalar_one_or_none()
