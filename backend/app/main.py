from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401 — register ORM models
from app.api.v1.router import api_router
from app.config import get_settings
from app.db.base import Base
from app.db.seed import seed_initial_data
from app.services.character_service import ensure_default_characters
from app.db.session import async_session_factory, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.database_url.startswith("sqlite"):
        from pathlib import Path

        Path("data").mkdir(parents=True, exist_ok=True)

    if settings.create_tables_on_startup:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    try:
        async with async_session_factory() as session:
            await seed_initial_data(session)
            await ensure_default_characters(session)
            await session.commit()
    except Exception:
        pass

    yield


app = FastAPI(
    title="Shorts Automation API",
    version="0.2.0",
    description="유튜브 쇼츠 자동 업로드 시스템 — Semi-auto 운영",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

_media_root = Path(settings.data_dir) / "jobs"
_media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media/jobs", StaticFiles(directory=str(_media_root)), name="job-media")


@app.get("/health")
async def health_check():
    from app.services.ffmpeg_path import ffmpeg_available, ffmpeg_version, resolve_ffmpeg
    from app.services.quota_manager import get_quota_status

    quota = await get_quota_status(settings)
    return {
        "status": "ok",
        "version": "1.0.0",
        "operation_mode": settings.default_operation_mode,
        "categories": settings.category_allowlist,
        "quota": quota,
        "ffmpeg": {
            "available": ffmpeg_available(),
            "path": resolve_ffmpeg(),
            "version": ffmpeg_version(),
        },
        "youtube_oauth_configured": settings.youtube_configured,
        "pilot_dry_run_upload": settings.pilot_dry_run_upload,
    }
