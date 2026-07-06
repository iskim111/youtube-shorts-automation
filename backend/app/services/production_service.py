"""TOP100·시리즈·참조 → Job + 시나리오 생성."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.enums import CopyrightRisk, TopicStatus
from app.models.script import Script
from app.models.topic_candidate import TopicCandidate
from app.services.character_service import get_characters_by_roles, next_character_code
from app.services.job_service import create_job_from_topic
from app.services.scenario_generator import SERIES_PRESETS, generate_dialogue_scenario, generate_trend_scenario
from app.services.topic_engine import next_topic_code


async def create_production_from_trending(
    session: AsyncSession,
    settings: Settings,
    *,
    channel,
    video_id: str,
    title: str,
    channel_title: str,
    url: str,
):
    script_content = await generate_trend_scenario(
        settings,
        video_title=title,
        channel_title=channel_title,
    )
    topic = await _create_topic(
        session,
        channel.id,
        hook_line=script_content.get("hook", title[:50]),
        category="comedy",
        keywords=[title[:30]],
        source_links=[url],
        breakdown={
            "topic_source": "trending",
            "trend_video_id": video_id,
            "trend_title": title,
            "video_mode": settings.video_mode,
        },
    )
    job = await _attach_job_script(session, topic, channel, script_content, settings)
    return topic, job, script_content


async def create_production_from_keyword(
    session: AsyncSession,
    settings: Settings,
    *,
    channel,
    keyword: str,
    source: str = "combined",
):
    script_content = await generate_trend_scenario(
        settings,
        video_title=keyword,
        channel_title="인기 검색어",
    )
    topic = await _create_topic(
        session,
        channel.id,
        hook_line=script_content.get("hook", keyword[:50]),
        category="comedy",
        keywords=[keyword],
        source_links=[f"keyword:{source}:{keyword}"],
        breakdown={
            "topic_source": "daily_keyword",
            "keyword": keyword,
            "keyword_source": source,
            "video_mode": settings.video_mode,
        },
    )
    job = await _attach_job_script(session, topic, channel, script_content, settings)
    return topic, job, script_content


async def create_series_episode(
    session: AsyncSession,
    settings: Settings,
    *,
    channel,
    preset: str,
    topic_hint: str = "",
):
    preset_def = SERIES_PRESETS.get(preset)
    if not preset_def:
        raise ValueError(f"알 수 없는 시리즈: {preset}")

    characters = await get_characters_by_roles(session, preset_def["roles"])
    if len(characters) < 2:
        raise ValueError("시리즈에 필요한 캐릭터가 Settings에 등록되지 않았습니다. HeyGen/ElevenLabs ID를 입력하세요.")

    topic_text = topic_hint or preset_def["label"]
    script_content = await generate_dialogue_scenario(
        settings,
        characters,
        topic=topic_text,
        preset=preset,
    )
    script_content["format"] = "dialogue"
    script_content["series_preset"] = preset
    script_content["character_codes"] = [c.code for c in characters]

    topic = await _create_topic(
        session,
        channel.id,
        hook_line=script_content.get("hook", topic_text[:50]),
        category="tips",
        keywords=[preset, "dialogue"],
        source_links=[f"series:{preset}"],
        breakdown={
            "topic_source": "series",
            "series_preset": preset,
            "video_mode": "ai_character",
        },
    )
    job = await _attach_job_script(session, topic, channel, script_content, settings)
    return topic, job, script_content, characters


async def _create_topic(
    session,
    channel_id,
    *,
    hook_line: str,
    category: str,
    keywords: list[str],
    source_links: list[str],
    breakdown: dict,
) -> TopicCandidate:
    code = await next_topic_code(session)
    topic = TopicCandidate(
        code=code,
        channel_id=channel_id,
        category=category,
        keyword_cluster=keywords,
        hook_line=hook_line,
        score_view_potential=80.0,
        score_final=75.0,
        score_breakdown=breakdown,
        status=TopicStatus.RECOMMENDED,
        source_links=source_links,
        copyright_risk=CopyrightRisk.LOW,
        ai_label_required=True,
    )
    session.add(topic)
    await session.flush()
    return topic


async def _attach_job_script(session, topic, channel, script_content, settings: Settings):
    job = await create_job_from_topic(session, topic, channel.operation_mode)
    job.render_template = "minimal_bottom"
    job.script = Script(
        job_id=job.id,
        content=script_content,
        duration_estimate_sec=script_content.get("target_duration_sec", 38),
    )
    session.add(job.script)

    job_dir = Path(settings.data_dir) / "jobs" / job.code
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "script.json").write_text(
        json.dumps(script_content, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    await session.flush()
    return job
