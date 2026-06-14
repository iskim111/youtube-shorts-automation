"""성과 수집 및 Topic Engine 피드백."""

from __future__ import annotations

import random
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import JobStatus
from app.models.job import Job
from app.models.performance_metric import PerformanceMetric
from app.models.enums import TopicStatus
from app.models.topic_candidate import TopicCandidate


async def collect_metrics_stub(session: AsyncSession, job: Job) -> PerformanceMetric:
    """실제 Analytics API 대신 파일럿용 스텁 수집."""
    upload = job.upload_record
    vid = upload.youtube_video_id if upload else None
    base = random.randint(50, 500) if vid else 0

    metric = PerformanceMetric(
        job_id=job.id,
        youtube_video_id=vid,
        views_1h=base,
        views_24h=int(base * 2.5),
        views_7d=int(base * 8),
        avg_view_duration_sec=round(random.uniform(12, 28), 1),
        retention_rate=round(random.uniform(0.35, 0.65), 4),
        ab_variant=job.ab_variant,
        collected_at=datetime.now(UTC),
    )
    session.add(metric)
    await session.flush()
    return metric


async def get_category_performance(session: AsyncSession) -> dict[str, dict]:
    """카테고리별 평균 성과 — Topic 가중치 보정용."""
    result = await session.execute(
        select(
            TopicCandidate.category,
            func.avg(PerformanceMetric.views_24h).label("avg_views"),
            func.avg(PerformanceMetric.retention_rate).label("avg_retention"),
            func.count(PerformanceMetric.id).label("sample_count"),
        )
        .join(Job, Job.topic_candidate_id == TopicCandidate.id)
        .join(PerformanceMetric, PerformanceMetric.job_id == Job.id)
        .where(Job.status == JobStatus.PUBLISHED)
        .group_by(TopicCandidate.category)
    )
    rows = result.all()
    return {
        row.category: {
            "avg_views_24h": float(row.avg_views or 0),
            "avg_retention": float(row.avg_retention or 0),
            "sample_count": int(row.sample_count or 0),
        }
        for row in rows
    }


async def get_overview_kpis(session: AsyncSession) -> dict:
    total_jobs = await session.scalar(select(func.count()).select_from(Job))
    published = await session.scalar(
        select(func.count()).select_from(Job).where(Job.status == JobStatus.PUBLISHED)
    )
    hold = await session.scalar(
        select(func.count()).select_from(Job).where(
            Job.status.in_([JobStatus.RIGHTS_HOLD, JobStatus.QA_HOLD])
        )
    )
    topics = await session.scalar(select(func.count()).select_from(TopicCandidate))
    approved_topics = await session.scalar(
        select(func.count()).select_from(TopicCandidate).where(
            TopicCandidate.status == TopicStatus.APPROVED
        )
    )
    conversion = (published / approved_topics * 100) if approved_topics else 0

    return {
        "total_jobs": total_jobs or 0,
        "published_jobs": published or 0,
        "hold_jobs": hold or 0,
        "publish_success_rate": round((published / total_jobs * 100) if total_jobs else 0, 1),
        "topic_to_publish_conversion": round(conversion, 1),
    }
