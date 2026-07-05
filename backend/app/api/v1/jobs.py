from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_effective_settings_dep
from app.config import Settings
from app.models.enums import JobStatus
from app.models.job import Job
from app.schemas.job import (
    JobChatRequest,
    JobChatResponse,
    JobDetailResponse,
    JobPreviewResponse,
    JobScheduleRequest,
    JobScriptUpdateRequest,
    JobSummaryResponse,
    PipelineRunResponse,
    PublishResponse,
)
from app.schemas.mappers import job_to_detail, job_to_summary
from app.services.pipeline_service import PipelineError, load_job_full, run_pipeline_to_qa
from app.services.job_chat_service import build_job_preview, chat_edit_script
from app.services.render_engine import RENDER_TEMPLATES
from app.services.recovery_service import retry_job_by_code
from app.services.upload_service import publish_job

router = APIRouter()


@router.get("", response_model=list[JobSummaryResponse])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Job)
        .options(
            selectinload(Job.topic_candidate),
            selectinload(Job.channel),
        )
        .order_by(Job.created_at.desc())
    )
    jobs = result.scalars().all()
    return [job_to_summary(j) for j in jobs]


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await load_job_full(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    return job_to_detail(job)


@router.get("/{job_id}/preview", response_model=JobPreviewResponse)
async def job_preview(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_effective_settings_dep),
):
    job = await load_job_full(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    data = build_job_preview(job, settings=settings)
    return JobPreviewResponse(**data)


@router.post("/{job_id}/chat", response_model=JobChatResponse)
async def job_chat(
    job_id: str,
    body: JobChatRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_effective_settings_dep),
):
    job = await load_job_full(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    result = await chat_edit_script(settings, job, body.message, body.history)
    if result.get("script") and job.script:
        job.script.content = result["script"]
        job.script.version += 1
        await db.commit()
    return JobChatResponse(**result)


@router.put("/{job_id}/script")
async def update_script(
    job_id: str,
    body: JobScriptUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    job = await load_job_full(db, job_id)
    if not job or not job.script:
        raise HTTPException(status_code=404, detail="대본을 찾을 수 없습니다.")
    job.script.content = body.script
    job.script.version += 1
    await db.commit()
    return {"job_id": job.code, "version": job.script.version}


@router.post("/{job_id}/run", response_model=PipelineRunResponse)
async def run_pipeline(
    job_id: str,
    use_async: bool = Query(False, alias="async"),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_effective_settings_dep),
):
    if settings.use_celery and use_async:
        from app.workers.tasks import run_pipeline as run_pipeline_task

        task = run_pipeline_task.delay(job_id)
        return PipelineRunResponse(
            job_id=job_id,
            status="QUEUED",
            message=f"Celery 큐 등록됨 (task_id={task.id})",
        )

    job = await load_job_full(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    try:
        await run_pipeline_to_qa(db, job, settings)
        await db.commit()
    except PipelineError as exc:
        await db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"파이프라인 오류: {exc}") from exc

    return PipelineRunResponse(
        job_id=job.code,
        status=job.status.value,
        message="생성 완료 — QA 승인 대기 (Semi-auto)",
    )


@router.post("/{job_id}/schedule")
async def schedule_job(
    job_id: str,
    body: JobScheduleRequest,
    db: AsyncSession = Depends(get_db),
):
    job = await load_job_full(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    if body.render_template and body.render_template in RENDER_TEMPLATES:
        job.render_template = body.render_template

    job.scheduled_publish_at = body.scheduled_publish_at
    if job.status == JobStatus.QA_PENDING:
        job.status = JobStatus.QA_APPROVED

    await db.commit()
    return {
        "job_id": job.code,
        "scheduled_publish_at": job.scheduled_publish_at.isoformat(),
        "render_template": job.render_template,
        "status": job.status.value,
    }


@router.post("/{job_id}/publish", response_model=PublishResponse)
async def publish(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_effective_settings_dep),
):
    job = await load_job_full(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    try:
        result = await publish_job(db, job, settings)
        await db.commit()
    except PipelineError as exc:
        await db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"업로드 오류: {exc}") from exc

    return PublishResponse(**result)


@router.post("/{job_id}/approve-qa")
async def approve_qa(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await load_job_full(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    job.status = JobStatus.QA_APPROVED
    await db.commit()
    return {"job_id": job.code, "status": job.status.value}


@router.post("/{job_id}/retry")
async def retry_job_endpoint(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_effective_settings_dep),
):
    try:
        result = await retry_job_by_code(db, job_id, settings)
        await db.commit()
    except PipelineError as exc:
        await db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.post("/{job_id}/hold")
async def hold_job(job_id: str, reason: str, db: AsyncSession = Depends(get_db)):
    job = await load_job_full(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    job.status = JobStatus.QA_HOLD
    job.hold_reason = reason
    await db.commit()
    return {"job_id": job.code, "status": job.status.value, "hold_reason": reason}
