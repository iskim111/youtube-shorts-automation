"""주제 소스: 트렌드(무료) / AI 생성(OpenAI 또는 무료 변형)."""

from __future__ import annotations

import json
import uuid
from typing import Literal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.data.trending_topics_ko import TRENDING_TOPIC_POOL
from app.models.enums import CopyrightRisk
from app.models.topic_candidate import TopicCandidate
from app.services.topic_engine import (
    TopicTemplate,
    filter_by_allowlist,
    get_recent_hooks,
    next_topic_code,
    score_template,
)

TopicSource = Literal["trending", "ai", "mixed"]

AI_VARIATION_SEEDS = [
    ("daily_pet", ["반려묘", "집"], "집에 혼자 있을 때 고양이가 하는 짓"),
    ("daily_pet", ["강아지", "산책"], "산책 가자고 하면 반응하는 강아지"),
    ("comedy", ["직장", "점심"], "점심 메뉴 고를 때 직장인 반응"),
    ("comedy", ["출근", "지하철"], "지하철에서 공감되는 그 순간"),
    ("food", ["간식", "야식"], "야식 땡길 때 1분 레시피"),
    ("food", ["컵라면", "꿀팁"], "컵라면 맛 2배 되는 방법"),
    ("tips", ["스마트폰", "꿀팁"], "폰 배터리 아끼는 숨은 설정"),
    ("tips", ["청소", "5분"], "5분 청소로 달라지는 공간"),
]


async def _generate_ai_topics_openai(
    settings: Settings,
    allowlist: list[str],
    limit: int,
) -> list[dict]:
    categories = ", ".join(allowlist)
    prompt = (
        f"한국 유튜브 쇼츠용 주제 {limit}개를 JSON 배열로 생성하세요. "
        f"카테고리: {categories}. "
        "각 항목: category, keyword_cluster(3개), hook_line(15자 내외), view_potential(70-95). "
        "저작권 안전한 일상/공감/팁/반려동물 소재만. JSON만 출력."
    )
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
            },
        )
        if resp.status_code != 200:
            return []
        content = resp.json()["choices"][0]["message"]["content"]
        start = content.find("[")
        end = content.rfind("]") + 1
        if start < 0 or end <= start:
            return []
        return json.loads(content[start:end])


def _generate_ai_topics_free(allowlist: list[str], limit: int) -> list[dict]:
    allowed = set(allowlist)
    items: list[dict] = []
    for cat, keywords, hook in AI_VARIATION_SEEDS:
        if cat not in allowed:
            continue
        items.append(
            {
                "category": cat,
                "keyword_cluster": keywords,
                "hook_line": hook,
                "view_potential": 78 + (len(hook) % 12),
            }
        )
        if len(items) >= limit:
            break
    return items[:limit]


async def _templates_for_source(
    source: TopicSource,
    settings: Settings,
    allowlist: list[str],
    limit: int,
) -> list[dict]:
    if source == "trending":
        templates = filter_by_allowlist(TRENDING_TOPIC_POOL, allowlist)
        templates.sort(key=lambda t: t.view_potential, reverse=True)
        return [
            {
                "category": t.category,
                "keyword_cluster": t.keyword_cluster,
                "hook_line": t.hook_line,
                "view_potential": t.view_potential,
                "competition": t.competition,
                "production": t.production,
                "copyright_safety": t.copyright_safety,
                "copyright_risk": t.copyright_risk,
                "ai_label_required": t.ai_label_required,
                "policy_flags": t.policy_flags,
                "source_links": t.source_links,
                "breakdown": {**t.breakdown, "topic_source": "trending"},
            }
            for t in templates[:limit]
        ]

    if source == "ai":
        raw: list[dict] = []
        if settings.openai_api_key:
            raw = await _generate_ai_topics_openai(settings, allowlist, limit)
        if not raw:
            raw = _generate_ai_topics_free(allowlist, limit)
        return [
            {
                "category": item["category"],
                "keyword_cluster": item.get("keyword_cluster", []),
                "hook_line": item["hook_line"],
                "view_potential": float(item.get("view_potential", 80)),
                "competition": 50.0,
                "production": 20.0,
                "copyright_safety": 88.0,
                "copyright_risk": CopyrightRisk.LOW,
                "ai_label_required": False,
                "policy_flags": [],
                "source_links": ["ai:generated"],
                "breakdown": {
                    "topic_source": "ai",
                    "ai_engine": "openai" if settings.openai_api_key else "free_variation",
                },
            }
            for item in raw[:limit]
        ]

    half = max(1, limit // 2)
    trending = await _templates_for_source("trending", settings, allowlist, half)
    ai = await _templates_for_source("ai", settings, allowlist, limit - half)
    combined = trending + ai
    combined.sort(key=lambda x: x["view_potential"], reverse=True)
    return combined[:limit]


async def generate_topics_from_source(
    session: AsyncSession,
    channel_id: uuid.UUID,
    allowlist: list[str],
    limit: int,
    source: TopicSource,
    settings: Settings,
) -> list[TopicCandidate]:
    from app.services.analytics_service import get_category_performance

    recent_hooks = await get_recent_hooks(session, channel_id)
    perf = await get_category_performance(session)
    raw_items = await _templates_for_source(source, settings, allowlist, limit)

    existing = set(recent_hooks)
    candidates: list[TopicCandidate] = []

    for item in raw_items:
        if item["hook_line"] in existing:
            continue
        if len(candidates) >= limit:
            break

        template = TopicTemplate(
            category=item["category"],
            keyword_cluster=item["keyword_cluster"],
            hook_line=item["hook_line"],
            view_potential=item["view_potential"],
            competition=item.get("competition", 50),
            production=item.get("production", 20),
            copyright_safety=item.get("copyright_safety", 88),
            copyright_risk=item.get("copyright_risk", CopyrightRisk.LOW),
            ai_label_required=item.get("ai_label_required", False),
            policy_flags=item.get("policy_flags", []),
            source_links=item.get("source_links", []),
            breakdown=item.get("breakdown", {"topic_source": source}),
        )
        scored = score_template(template, recent_hooks, perf)
        code = await next_topic_code(session)

        candidate = TopicCandidate(
            code=code,
            channel_id=channel_id,
            category=template.category,
            keyword_cluster=template.keyword_cluster,
            hook_line=template.hook_line,
            score_view_potential=template.view_potential,
            score_competition=template.competition,
            score_production=template.production,
            score_copyright_safety=template.copyright_safety,
            score_final=scored["final_score"],
            score_breakdown=template.breakdown,
            status=scored["status"],
            source_links=template.source_links,
            ai_label_required=template.ai_label_required,
            copyright_risk=template.copyright_risk,
            similarity_penalty=scored["similarity_penalty"],
            policy_penalty=scored["policy_penalty"],
        )
        session.add(candidate)
        candidates.append(candidate)
        recent_hooks.append(template.hook_line)

    await session.flush()
    return candidates
