"""애셋 검색·다운로드 (Pexels → Pixabay fallback)."""

from __future__ import annotations

from pathlib import Path

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.integrations.pexels import search_videos as pexels_search
from app.integrations.pixabay import search_videos as pixabay_search
from app.models.asset import Asset
from app.models.job import Job
from app.models.topic_candidate import TopicCandidate

CATEGORY_QUERIES = {
    "comedy": "office funny",
    "food": "cooking food",
    "daily_pet": "cat pet",
    "tips": "smartphone technology",
}


async def _download_file(url: str, dest: Path) -> bool:
    try:
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                dest.write_bytes(resp.content)
                return True
    except Exception:
        pass
    return False


async def fetch_assets_for_job(
    session: AsyncSession,
    job: Job,
    topic: TopicCandidate,
    settings: Settings,
    job_dir: Path,
) -> list[Asset]:
    query = CATEGORY_QUERIES.get(topic.category, " ".join(topic.keyword_cluster[:2]))
    candidates = await pexels_search(settings, query, per_page=2)
    if not candidates:
        candidates = await pixabay_search(settings, query, per_page=2)

    assets: list[Asset] = []
    assets_dir = job_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    for i, item in enumerate(candidates[:2]):
        download_url = item.get("download_url")
        if not download_url:
            continue
        dest = assets_dir / f"clip_{i}.mp4"
        if await _download_file(download_url, dest):
            asset = Asset(
                job_id=job.id,
                source_type=item["source_type"],
                source_url=item.get("source_url"),
                storage_uri=str(dest),
                license_status=item.get("license_status", "low"),
                license_proof_uri=item.get("source_url"),
                asset_metadata={
                    "photographer": item.get("photographer", ""),
                    "width": item.get("width"),
                    "height": item.get("height"),
                },
            )
            session.add(asset)
            assets.append(asset)

    if not assets:
        placeholder = Asset(
            job_id=job.id,
            source_type="generated",
            source_url=None,
            storage_uri=None,
            license_status="low",
            asset_metadata={"note": "no stock API key — color background fallback"},
        )
        session.add(placeholder)
        assets.append(placeholder)

    await session.flush()
    return assets
