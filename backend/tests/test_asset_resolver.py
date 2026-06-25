import uuid

import pytest
from unittest.mock import AsyncMock, patch

from app.config import Settings
from app.integrations.asset_types import ResolvedAsset
from app.models.topic_candidate import TopicCandidate
from app.services.asset_resolver import resolve_scene_assets
from app.services.script_generator import generate_script


@pytest.fixture
def topic() -> TopicCandidate:
    return TopicCandidate(
        code="T-001",
        channel_id=uuid.uuid4(),
        category="daily_pet",
        keyword_cluster=["고양이", "출근", "집사"],
        hook_line="집사 출근할 때 고양이 속마음",
        score_final=80.0,
    )


def test_script_includes_visual_prompt(topic: TopicCandidate):
    script = generate_script(topic)
    assert all("visual_prompt" in s for s in script["scenes"])
    assert "9:16" in script["scenes"][0]["visual_prompt"]


@pytest.mark.asyncio
async def test_resolve_free_only_uses_stock(tmp_path, topic: TopicCandidate):
    settings = Settings(pexels_api_key="test-key", asset_strategy="free_only")
    script = generate_script(topic)

    fake = ResolvedAsset(
        source_type="pexels",
        storage_uri=str(tmp_path / "clip.mp4"),
        media_kind="video",
        provider="pexels",
    )
    (tmp_path / "clip.mp4").write_bytes(b"fake")

    with patch(
        "app.services.asset_resolver._try_stock_clip",
        new=AsyncMock(return_value=fake),
    ):
        assets = await resolve_scene_assets(settings, topic, script, tmp_path)

    assert len(assets) == 4
    assert all(a.provider == "pexels" for a in assets)


@pytest.mark.asyncio
async def test_resolve_hybrid_prefers_ai_for_first_scene(tmp_path, topic: TopicCandidate):
    settings = Settings(
        openai_api_key="sk-test",
        asset_strategy="hybrid",
        ai_max_scenes_per_job=1,
    )
    script = generate_script(topic)

    ai_asset = ResolvedAsset(
        source_type="ai_image",
        storage_uri=str(tmp_path / "scene_1_ai.png"),
        media_kind="image",
        scene_seq=1,
        provider="openai",
        metadata={"ai_generated": True},
    )
    (tmp_path / "scene_1_ai.png").write_bytes(b"png")

    stock = ResolvedAsset(
        source_type="pexels",
        storage_uri=str(tmp_path / "stock.mp4"),
        media_kind="video",
        provider="pexels",
    )
    (tmp_path / "stock.mp4").write_bytes(b"mp4")

    async def fake_ai(settings, prompt, job_dir, seq, duration):
        if seq == 1:
            return ai_asset
        return None

    with (
        patch("app.services.asset_resolver._try_ai_for_scene", side_effect=fake_ai),
        patch(
            "app.services.asset_resolver._try_stock_clip",
            new=AsyncMock(return_value=stock),
        ),
    ):
        assets = await resolve_scene_assets(settings, topic, script, tmp_path)

    assert assets[0].source_type == "ai_image"
    assert assets[1].source_type == "pexels"
