"""에셋 전략: 무료 스톡 기본 + (선택) AI 이미지/영상."""

from __future__ import annotations

from pathlib import Path

import httpx

from app.config import Settings
from app.integrations.ai_video import generate_scene_video
from app.integrations.asset_types import ResolvedAsset
from app.integrations.openai_images import generate_scene_image
from app.integrations.pexels import search_videos as pexels_search
from app.integrations.pixabay import search_videos as pixabay_search
from app.models.topic_candidate import TopicCandidate

CATEGORY_QUERIES = {
    "comedy": "office funny",
    "food": "cooking food",
    "daily_pet": "cat pet",
    "tips": "smartphone technology",
}


async def download_asset_file(url: str, dest: Path) -> bool:
    try:
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(resp.content)
                return dest.exists() and dest.stat().st_size > 0
    except Exception:
        pass
    return False


def _stock_query(topic: TopicCandidate, scene: dict) -> str:
    hint = scene.get("visual_hint") or ""
    base = CATEGORY_QUERIES.get(topic.category, " ".join(topic.keyword_cluster[:2]))
    if hint and hint not in ("keyword overlay", "reaction beat", "cta end card"):
        return f"{base} {hint}".strip()
    return base


async def _try_stock_clip(
    settings: Settings,
    query: str,
    dest: Path,
) -> ResolvedAsset | None:
    candidates = await pexels_search(settings, query, per_page=2)
    if not candidates:
        candidates = await pixabay_search(settings, query, per_page=2)
    for item in candidates:
        url = item.get("download_url")
        if url and await download_asset_file(url, dest):
            return ResolvedAsset(
                source_type=item["source_type"],
                storage_uri=str(dest),
                source_url=item.get("source_url"),
                license_status=item.get("license_status", "low"),
                media_kind="video",
                provider=item["source_type"],
                metadata={
                    "photographer": item.get("photographer", ""),
                    "query": query,
                },
            )
    return None


async def _try_ai_for_scene(
    settings: Settings,
    prompt: str,
    job_dir: Path,
    scene_seq: int,
    duration_sec: int,
) -> ResolvedAsset | None:
    assets_dir = job_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    if settings.ai_video_configured:
        video_dest = assets_dir / f"scene_{scene_seq}_ai.mp4"
        if await generate_scene_video(
            settings, prompt, video_dest, duration_sec=min(duration_sec, 10)
        ):
            return ResolvedAsset(
                source_type="ai_video",
                storage_uri=str(video_dest),
                license_status="medium",
                media_kind="video",
                scene_seq=scene_seq,
                duration_sec=duration_sec,
                provider=settings.ai_video_provider,
                metadata={"prompt": prompt, "ai_generated": True},
            )

    if settings.ai_image_configured:
        image_dest = assets_dir / f"scene_{scene_seq}_ai.png"
        if await generate_scene_image(settings, prompt, image_dest):
            return ResolvedAsset(
                source_type="ai_image",
                storage_uri=str(image_dest),
                license_status="medium",
                media_kind="image",
                scene_seq=scene_seq,
                duration_sec=duration_sec,
                provider=settings.ai_image_provider,
                metadata={"prompt": prompt, "ai_generated": True},
            )

    return None


def _placeholder(scene_seq: int, duration_sec: int, note: str) -> ResolvedAsset:
    return ResolvedAsset(
        source_type="generated",
        storage_uri=None,
        license_status="low",
        media_kind="placeholder",
        scene_seq=scene_seq,
        duration_sec=duration_sec,
        provider="fallback",
        metadata={"note": note},
    )


async def resolve_scene_assets(
    settings: Settings,
    topic: TopicCandidate,
    script_content: dict,
    job_dir: Path,
) -> list[ResolvedAsset]:
    """장면별 에셋 resolve. strategy에 따라 무료 스톡 / AI / fallback."""
    scenes = script_content.get("scenes") or []
    if not scenes:
        scenes = [{"seq": 1, "duration_sec": 15, "visual_prompt": topic.hook_line, "visual_hint": ""}]

    strategy = settings.asset_strategy
    assets_dir = job_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    resolved: list[ResolvedAsset] = []

    for scene in scenes:
        seq = int(scene.get("seq", len(resolved) + 1))
        duration = int(scene.get("duration_sec", 8))
        prompt = scene.get("visual_prompt") or topic.hook_line
        query = _stock_query(topic, scene)
        stock_dest = assets_dir / f"scene_{seq}_stock.mp4"

        picked: ResolvedAsset | None = None
        use_ai = strategy in ("hybrid", "ai_preferred") and (
            strategy == "ai_preferred" or seq <= settings.ai_max_scenes_per_job
        )

        if use_ai:
            picked = await _try_ai_for_scene(settings, prompt, job_dir, seq, duration)
            if picked is None and strategy == "ai_preferred":
                picked = await _try_stock_clip(settings, query, stock_dest)

        if picked is None and strategy in ("free_only", "hybrid", "ai_preferred"):
            picked = await _try_stock_clip(settings, query, stock_dest)

        if picked is None:
            picked = _placeholder(
                seq,
                duration,
                "no stock API / AI — color background fallback",
            )

        picked.scene_seq = seq
        picked.duration_sec = duration
        resolved.append(picked)

    return resolved
