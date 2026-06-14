from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.analytics_service import get_category_performance, get_overview_kpis
from app.services.quota_manager import get_quota_status
from app.config import Settings, get_settings

router = APIRouter()


class OverviewResponse(BaseModel):
    kpis: dict
    quota: dict
    category_performance: dict


@router.get("/overview", response_model=OverviewResponse)
async def analytics_overview(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    kpis = await get_overview_kpis(db)
    quota = await get_quota_status(settings)
    perf = await get_category_performance(db)
    return OverviewResponse(kpis=kpis, quota=quota, category_performance=perf)
