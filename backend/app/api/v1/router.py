from fastapi import APIRouter

from app.api.v1 import analytics, audit, auth, calendar, channels, jobs, rights, setup, topics

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(channels.router, prefix="/channels", tags=["channels"])
api_router.include_router(rights.router, prefix="/rights", tags=["rights"])
api_router.include_router(calendar.router, prefix="/uploads/calendar", tags=["calendar"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(setup.router, prefix="/setup", tags=["setup"])
