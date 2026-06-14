"""Celery 비동기 작업."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.config import get_settings
from app.db.session import async_session_factory
from app.services.pipeline_service import PipelineError, load_job_full, run_pipeline_to_qa
from app.services.upload_service import publish_job
from app.workers.celery_app import celery_app


def _run_async(coro):
    return asyncio.run(coro)


@celery_app.task(name="app.workers.tasks.run_pipeline", bind=True, max_retries=3)
def run_pipeline(self, job_code: str) -> dict:
    settings = get_settings()

    async def _execute():
        async with async_session_factory() as session:
            job = await load_job_full(session, job_code)
            if not job:
                return {"error": "job not found", "job_code": job_code}
            try:
                await run_pipeline_to_qa(session, job, settings)
                await session.commit()
                return {"job_code": job_code, "status": job.status.value}
            except PipelineError as exc:
                await session.commit()
                return {"job_code": job_code, "error": str(exc), "stage": exc.stage}
            except Exception as exc:
                await session.rollback()
                raise exc

    try:
        return _run_async(_execute())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30) from exc


@celery_app.task(name="app.workers.tasks.sync_analytics")
def sync_analytics() -> dict:
    settings = get_settings()

    async def _execute():
        from sqlalchemy import select

        from app.models.enums import JobStatus
        from app.models.job import Job
        from app.services.analytics_service import collect_metrics_stub
        from app.services.pipeline_service import load_job_full

        synced = 0
        async with async_session_factory() as session:
            result = await session.execute(
                select(Job).where(Job.status == JobStatus.PUBLISHED).limit(20)
            )
            for job in result.scalars().all():
                full = await load_job_full(session, job.code)
                if full and not full.performance_metrics:
                    await collect_metrics_stub(session, full)
                    synced += 1
            await session.commit()
        return {"synced": synced}

    return _run_async(_execute())


@celery_app.task(name="app.workers.tasks.publish_due_jobs")
def publish_due_jobs() -> dict:
    settings = get_settings()

    async def _execute():
        from sqlalchemy import select

        from app.models.enums import JobStatus
        from app.models.job import Job

        published = []
        async with async_session_factory() as session:
            now = datetime.now(UTC)
            result = await session.execute(
                select(Job).where(
                    Job.status == JobStatus.QA_APPROVED,
                    Job.scheduled_publish_at.isnot(None),
                    Job.scheduled_publish_at <= now,
                )
            )
            jobs = result.scalars().all()
            for job in jobs:
                full = await load_job_full(session, job.code)
                if not full:
                    continue
                try:
                    res = await publish_job(session, full, settings)
                    await session.commit()
                    published.append(res)
                except PipelineError:
                    await session.commit()
                except Exception:
                    await session.rollback()
        return {"published_count": len(published), "jobs": published}

    return _run_async(_execute())
