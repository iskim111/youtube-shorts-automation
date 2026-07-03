import pytest

from app.config import Settings
from app.services.topic_sources import _generate_ai_topics_free, _templates_for_source


@pytest.mark.asyncio
async def test_trending_source_sorted_by_view_potential():
    settings = Settings()
    items = await _templates_for_source("trending", settings, ["daily_pet", "comedy"], limit=5)
    assert len(items) >= 1
    assert items[0]["breakdown"]["topic_source"] == "trending"
    scores = [i["view_potential"] for i in items]
    assert scores == sorted(scores, reverse=True)


def test_ai_free_variation():
    items = _generate_ai_topics_free(["daily_pet"], limit=2)
    assert len(items) >= 1
    assert "hook_line" in items[0]


@pytest.mark.asyncio
async def test_mixed_source():
    settings = Settings()
    items = await _templates_for_source("mixed", settings, ["daily_pet", "food", "tips"], limit=4)
    assert len(items) >= 2
    sources = {i["breakdown"]["topic_source"] for i in items}
    assert "trending" in sources or "ai" in sources
