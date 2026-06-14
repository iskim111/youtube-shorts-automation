"""주제 선정 엔진: Allowlist + 스코어링 + 하드 필터."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CopyrightRisk, TopicStatus
from app.models.topic_candidate import TopicCandidate

Category = Literal["comedy", "food", "daily_pet", "tips"]

WEIGHTS = {
    "view_potential": 0.40,
    "competition_inverse": 0.25,
    "production_inverse": 0.20,
    "copyright_safety": 0.15,
}

HIGH_RISK_CATEGORIES = {"kpop", "sports_fandom"}

SIMILARITY_THRESHOLD = 0.55
SIMILARITY_PENALTY_MIN = 10
SIMILARITY_PENALTY_MAX = 30


@dataclass(frozen=True)
class TopicTemplate:
    category: Category
    keyword_cluster: list[str]
    hook_line: str
    view_potential: float
    competition: float
    production: float
    copyright_safety: float
    copyright_risk: CopyrightRisk
    ai_label_required: bool
    policy_flags: list[str]
    source_links: list[str]
    breakdown: dict[str, float]


TOPIC_TEMPLATES: list[TopicTemplate] = [
    TopicTemplate(
        category="comedy",
        keyword_cluster=["직장인", "회식", "상사"],
        hook_line="회식 끝나고 꼭 나오는 그 한마디",
        view_potential=86,
        competition=58,
        production=25,
        copyright_safety=88,
        copyright_risk=CopyrightRisk.LOW,
        ai_label_required=False,
        policy_flags=[],
        source_links=[],
        breakdown={"trend_velocity": 0.72, "channel_fit": 0.91, "hook_score": 0.88},
    ),
    TopicTemplate(
        category="food",
        keyword_cluster=["3재료", "야식", "전자레인지"],
        hook_line="전자레인지 2분 야식",
        view_potential=82,
        competition=63,
        production=18,
        copyright_safety=90,
        copyright_risk=CopyrightRisk.LOW,
        ai_label_required=False,
        policy_flags=[],
        source_links=[],
        breakdown={"trend_velocity": 0.68, "channel_fit": 0.85, "hook_score": 0.82},
    ),
    TopicTemplate(
        category="daily_pet",
        keyword_cluster=["반려묘", "출근", "집사"],
        hook_line="집사 출근할 때 고양이 속마음",
        view_potential=77,
        competition=47,
        production=16,
        copyright_safety=92,
        copyright_risk=CopyrightRisk.LOW,
        ai_label_required=False,
        policy_flags=[],
        source_links=[],
        breakdown={"trend_velocity": 0.61, "channel_fit": 0.88, "hook_score": 0.79},
    ),
    TopicTemplate(
        category="tips",
        keyword_cluster=["생활팁", "스마트폰", "배터리"],
        hook_line="배터리 오래 가는 설정 3가지",
        view_potential=74,
        competition=52,
        production=22,
        copyright_safety=85,
        copyright_risk=CopyrightRisk.LOW,
        ai_label_required=False,
        policy_flags=[],
        source_links=[],
        breakdown={"trend_velocity": 0.55, "channel_fit": 0.80, "hook_score": 0.76},
    ),
    TopicTemplate(
        category="comedy",
        keyword_cluster=["알바", "손님", "카페"],
        hook_line="카페 알바생만 아는 그 순간",
        view_potential=80,
        competition=55,
        production=20,
        copyright_safety=90,
        copyright_risk=CopyrightRisk.LOW,
        ai_label_required=False,
        policy_flags=[],
        source_links=[],
        breakdown={"trend_velocity": 0.65, "channel_fit": 0.87, "hook_score": 0.84},
    ),
]


def compute_final_score(
    view_potential: float,
    competition: float,
    production: float,
    copyright_safety: float,
    similarity_penalty: float = 0,
    policy_penalty: float = 0,
) -> float:
    competition_inverse = 100 - competition
    production_inverse = 100 - production
    raw = (
        WEIGHTS["view_potential"] * view_potential
        + WEIGHTS["competition_inverse"] * competition_inverse
        + WEIGHTS["production_inverse"] * production_inverse
        + WEIGHTS["copyright_safety"] * copyright_safety
        - similarity_penalty
        - policy_penalty
    )
    return round(max(0, min(100, raw)), 1)


def hook_similarity(a: str, b: str) -> float:
    """간단한 토큰 겹침 비율 (0~1)."""
    tokens_a = set(a.replace("/", " ").split())
    tokens_b = set(b.replace("/", " ").split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def compute_similarity_penalty(hook_line: str, recent_hooks: list[str]) -> float:
    if not recent_hooks:
        return 0.0
    max_sim = max(hook_similarity(hook_line, h) for h in recent_hooks)
    if max_sim < SIMILARITY_THRESHOLD:
        return 0.0
    scale = (max_sim - SIMILARITY_THRESHOLD) / (1 - SIMILARITY_THRESHOLD)
    return round(SIMILARITY_PENALTY_MIN + scale * (SIMILARITY_PENALTY_MAX - SIMILARITY_PENALTY_MIN), 1)


def resolve_status(
    copyright_risk: CopyrightRisk,
    similarity_penalty: float,
    policy_penalty: float,
    category: str,
    final_score: float,
) -> TopicStatus:
    if copyright_risk == CopyrightRisk.HIGH:
        return TopicStatus.REVIEW_REQUIRED
    if category in HIGH_RISK_CATEGORIES:
        return TopicStatus.REVIEW_REQUIRED
    if similarity_penalty >= SIMILARITY_PENALTY_MAX * 0.8:
        return TopicStatus.ON_HOLD
    if policy_penalty > 0:
        return TopicStatus.ON_HOLD
    if copyright_risk == CopyrightRisk.MEDIUM:
        return TopicStatus.REVIEW_REQUIRED
    if final_score >= 70:
        return TopicStatus.RECOMMENDED
    return TopicStatus.GENERATED


async def get_recent_hooks(session: AsyncSession, channel_id: uuid.UUID, limit: int = 20) -> list[str]:
    result = await session.execute(
        select(TopicCandidate.hook_line)
        .where(TopicCandidate.channel_id == channel_id)
        .order_by(TopicCandidate.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def next_topic_code(session: AsyncSession) -> str:
    from sqlalchemy import func

    result = await session.execute(select(func.count()).select_from(TopicCandidate))
    count = result.scalar() or 0
    return f"T-{count + 1:04d}"


def filter_by_allowlist(templates: list[TopicTemplate], allowlist: list[str]) -> list[TopicTemplate]:
    allowed = set(allowlist)
    return [t for t in templates if t.category in allowed]


def performance_boost(category: str, perf: dict[str, dict]) -> float:
    """성과 피드백 기반 가산점 (최대 +10)."""
    data = perf.get(category)
    if not data or data.get("sample_count", 0) < 1:
        return 0.0
    views = data.get("avg_views_24h", 0)
    retention = data.get("avg_retention", 0)
    return round(min(10.0, views / 80 + retention * 10), 1)


def score_template(
    template: TopicTemplate,
    recent_hooks: list[str],
    perf: dict[str, dict] | None = None,
) -> dict:
    similarity_penalty = compute_similarity_penalty(template.hook_line, recent_hooks)
    policy_penalty = 15.0 if template.policy_flags else 0.0
    boost = performance_boost(template.category, perf or {})
    final_score = compute_final_score(
        template.view_potential,
        template.competition,
        template.production,
        template.copyright_safety,
        similarity_penalty,
        policy_penalty,
    )
    final_score = round(min(100, final_score + boost), 1)
    status = resolve_status(
        template.copyright_risk,
        similarity_penalty,
        policy_penalty,
        template.category,
        final_score,
    )
    return {
        "similarity_penalty": similarity_penalty,
        "policy_penalty": policy_penalty,
        "final_score": final_score,
        "status": status,
    }


async def generate_topic_candidates(
    session: AsyncSession,
    channel_id: uuid.UUID,
    allowlist: list[str],
    limit: int = 5,
) -> list[TopicCandidate]:
    from app.services.analytics_service import get_category_performance

    recent_hooks = await get_recent_hooks(session, channel_id)
    templates = filter_by_allowlist(TOPIC_TEMPLATES, allowlist)
    perf = await get_category_performance(session)

    existing_hooks = {h for h in recent_hooks}
    candidates: list[TopicCandidate] = []

    for template in templates:
        if template.hook_line in existing_hooks:
            continue
        if len(candidates) >= limit:
            break

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
