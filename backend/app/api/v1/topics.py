from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_effective_settings_dep
from app.config import Settings
from app.models.channel import Channel
from app.models.enums import TopicStatus
from app.models.topic_candidate import TopicCandidate
from app.schemas.mappers import topic_to_response
from app.schemas.topic import TopicCandidateResponse, TopicGenerateRequest
from app.services.job_service import create_job_from_topic, get_topic_by_code
from app.services.topic_sources import generate_topics_from_source

router = APIRouter()


@router.get("", response_model=list[TopicCandidateResponse])
async def list_topics(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(TopicCandidate).order_by(TopicCandidate.score_final.desc())
    if status:
        query = query.where(TopicCandidate.status == TopicStatus(status))
    result = await db.execute(query)
    topics = result.scalars().all()
    return [topic_to_response(t) for t in topics]


@router.post("/generate", response_model=list[TopicCandidateResponse])
async def generate_topics(
    body: TopicGenerateRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_effective_settings_dep),
):
    channel = await db.get(Channel, body.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
    candidates = await generate_topics_from_source(
        db,
        channel.id,
        channel.category_allowlist,
        limit=body.limit,
        source=body.source,
        settings=settings,
    )
    await db.commit()
    return [topic_to_response(c) for c in candidates]


@router.post("/{topic_id}/approve")
async def approve_topic(topic_id: str, db: AsyncSession = Depends(get_db)):
    topic = await get_topic_by_code(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")
    if topic.status == TopicStatus.ON_HOLD:
        raise HTTPException(status_code=400, detail="보류 상태 주제는 검수 후 승인하세요.")

    channel = await db.get(Channel, topic.channel_id)
    job = await create_job_from_topic(db, topic, channel.operation_mode)
    await db.commit()
    return {
        "topic_id": topic.code,
        "job_id": job.code,
        "status": job.status.value,
    }


@router.post("/{topic_id}/reject")
async def reject_topic(topic_id: str, db: AsyncSession = Depends(get_db)):
    topic = await get_topic_by_code(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="주제를 찾을 수 없습니다.")
    topic.status = TopicStatus.REJECTED
    await db.commit()
    return {"topic_id": topic.code, "status": topic.status.value}
