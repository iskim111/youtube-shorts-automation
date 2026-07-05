from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_effective_settings_dep
from app.config import Settings
from app.models.channel import Channel
from app.schemas.reference import (
    ReferenceAnalyzeRequest,
    ReferenceAnalyzeResponse,
    ReferenceCreateJobRequest,
    ReferenceCreateJobResponse,
)
from app.services.reference_analyzer_service import (
    ReferenceAnalyzerError,
    analyze_reference_url,
    create_job_from_reference,
)

router = APIRouter()


@router.post("/analyze", response_model=ReferenceAnalyzeResponse)
async def analyze_reference(
    body: ReferenceAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_effective_settings_dep),
):
    channel = await db.get(Channel, body.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
    try:
        analysis = await analyze_reference_url(settings, body.url, channel.category_allowlist)
    except ReferenceAnalyzerError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ReferenceAnalyzeResponse(
        video_id=analysis["video_id"],
        url=analysis["url"],
        title=analysis["title"],
        author_name=analysis.get("author_name"),
        thumbnail_url=analysis.get("thumbnail_url"),
        category=analysis["category"],
        hook_line=analysis["hook_line"],
        keyword_cluster=analysis["keyword_cluster"],
        style_notes=analysis.get("style_notes", ""),
        script=analysis["script"],
    )


@router.post("/create-job", response_model=ReferenceCreateJobResponse)
async def create_job_from_reference_url(
    body: ReferenceCreateJobRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_effective_settings_dep),
):
    channel = await db.get(Channel, body.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")
    try:
        topic, job, analysis = await create_job_from_reference(
            db,
            channel,
            settings,
            body.url,
            analysis=body.analysis,
        )
    except ReferenceAnalyzerError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    return ReferenceCreateJobResponse(
        topic_id=topic.code,
        job_id=job.code,
        status=job.status.value,
        hook_line=topic.hook_line,
        reference_url=analysis["url"],
        reference_title=analysis["title"],
    )
