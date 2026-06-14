import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_ROOT = Path(__file__).resolve().parent / "test_runtime"
TEST_ROOT.mkdir(exist_ok=True)
(TEST_ROOT / "data").mkdir(exist_ok=True)


def _configure_test_db() -> None:
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(TEST_ROOT / 'test.db').as_posix()}"
    os.environ["DATA_DIR"] = str(TEST_ROOT / "data")
    os.environ["CREATE_TABLES_ON_STARTUP"] = "true"
    os.environ["PILOT_DRY_RUN_UPLOAD"] = "true"

    from app.config import get_settings

    get_settings.cache_clear()

    import app.db.session as session_module

    settings = get_settings()
    session_module.engine = create_async_engine(settings.database_url, echo=False)
    session_module.async_session_factory = async_sessionmaker(
        session_module.engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.fixture
async def client():
    _configure_test_db()

    from app.db.base import Base
    from app.db.seed import seed_initial_data
    from app.main import app
    import app.db.session as session_module

    async with session_module.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with session_module.async_session_factory() as session:
        await seed_initial_data(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
