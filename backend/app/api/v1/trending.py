from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.channel import Channel
from app.schemas.character import ProductionCreateResponse, TrendingCreateRequest
from app.services.daily_keywords_service import fetch_daily_keywords
from app.services.production_service import create_production_from_keyword, create_production_from_trending
from app.services.settings_store import get_effective_settings
from app.services.trending_shorts_service import fetch_trending_shorts

router = APIRouter()


@router.get("/keywords")
async def list_daily_keywords(
    limit: int = Query(default=100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    settings = await get_effective_settings(db)
    try:
        data = await fetch_daily_keywords(settings, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"인기 검색어 수집 실패: {e}") from e
    return {
        "google": data.get("google", []),
        "naver": data.get("naver", []),
        "combined": data.get("combined", []),
        "fetched_at": data.get("fetched_at"),
    }


@router.get("/shorts")
async def list_trending_shorts(
    limit: int = Query(default=100, ge=1, le=100),
    region: str = Query(default="KR"),
    keyword: str | None = Query(default=None, min_length=1, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    settings = await get_effective_settings(db)
    try:
        result = await fetch_trending_shorts(settings, limit=limit, region=region, keyword=keyword)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return result


@router.post("/shorts/{video_id}/create-production", response_model=ProductionCreateResponse)
async def create_from_trending(
    video_id: str,
    body: TrendingCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    settings = await get_effective_settings(db)
    channel = await db.get(Channel, body.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")

    try:
        trending = await fetch_trending_shorts(settings, limit=100)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    item = next((t for t in trending["items"] if t["video_id"] == video_id), None)
    if not item:
        item = {
            "video_id": video_id,
            "url": f"https://www.youtube.com/shorts/{video_id}",
            "title": video_id,
            "channel_title": "",
        }

    topic, job, script = await create_production_from_trending(
        db,
        settings,
        channel=channel,
        video_id=item["video_id"],
        title=item["title"],
        channel_title=item.get("channel_title", ""),
        url=item["url"],
    )
    await db.commit()
    return ProductionCreateResponse(
        topic_id=topic.code,
        job_id=job.code,
        status=job.status.value,
        hook_line=topic.hook_line,
        script_format=script.get("format", "monologue"),
    )


@router.post("/keywords/create-production", response_model=ProductionCreateResponse)
async def create_from_keyword(
    body: TrendingCreateRequest,
    keyword: str = Query(..., min_length=1, max_length=100),
    source: str = Query(default="combined"),
    db: AsyncSession = Depends(get_db),
):
    settings = await get_effective_settings(db)
    channel = await db.get(Channel, body.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다.")

    topic, job, script = await create_production_from_keyword(
        db,
        settings,
        channel=channel,
        keyword=keyword,
        source=source,
    )
    await db.commit()
    return ProductionCreateResponse(
        topic_id=topic.code,
        job_id=job.code,
        status=job.status.value,
        hook_line=topic.hook_line,
        script_format=script.get("format", "monologue"),
    )
