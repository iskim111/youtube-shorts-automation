"""Job 에셋 DB 저장 — resolve는 asset_resolver가 담당."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.integrations.asset_types import ResolvedAsset
from app.models.asset import Asset
from app.models.job import Job
from app.models.topic_candidate import TopicCandidate
from app.services.asset_resolver import resolve_scene_assets

CATEGORY_QUERIES = {
    "comedy": "office funny",
    "food": "cooking food",
    "daily_pet": "cat pet",
    "tips": "smartphone technology",
}


def _resolved_to_model(job: Job, item: ResolvedAsset) -> Asset:
    return Asset(
        job_id=job.id,
        source_type=item.source_type,
        source_url=item.source_url,
        storage_uri=item.storage_uri,
        license_status=item.license_status,
        license_proof_uri=item.source_url,
        asset_metadata={
            **item.metadata,
            "scene_seq": item.scene_seq,
            "duration_sec": item.duration_sec,
            "media_kind": item.media_kind,
            "provider": item.provider,
        },
    )


async def fetch_assets_for_job(
    session: AsyncSession,
    job: Job,
    topic: TopicCandidate,
    settings: Settings,
    job_dir: Path,
    script_content: dict | None = None,
) -> list[Asset]:
    content = script_content or (job.script.content if job.script else {})
    resolved = await resolve_scene_assets(settings, topic, content, job_dir)

    assets: list[Asset] = []
    for item in resolved:
        asset = _resolved_to_model(job, item)
        session.add(asset)
        assets.append(asset)

    await session.flush()
    return assets
