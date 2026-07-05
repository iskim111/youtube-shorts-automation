"""YouTube Shorts 참조 URL 분석 → 대본 구조 생성."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings
from app.models.enums import CopyrightRisk, TopicStatus
from app.models.script import Script
from app.models.topic_candidate import TopicCandidate
from app.services.job_service import create_job_from_topic
from app.services.topic_engine import next_topic_code as topic_code

_VIDEO_ID_RE = re.compile(
    r"(?:youtube\.com/shorts/|youtu\.be/|youtube\.com/watch\?(?:[^&]*&)*v=)([a-zA-Z0-9_-]{11})"
)


class ReferenceAnalyzerError(Exception):
    pass


def parse_youtube_video_id(url: str) -> str:
    match = _VIDEO_ID_RE.search(url.strip())
    if not match:
        raise ReferenceAnalyzerError("유효한 YouTube Shorts/영상 URL이 아닙니다.")
    return match.group(1)


def canonical_shorts_url(video_id: str) -> str:
    return f"https://www.youtube.com/shorts/{video_id}"


async def fetch_video_metadata(url: str) -> dict[str, Any]:
    video_id = parse_youtube_video_id(url)
    canonical = canonical_shorts_url(video_id)
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        resp = await client.get(
            "https://www.youtube.com/oembed",
            params={"url": canonical, "format": "json"},
        )
        if resp.status_code != 200:
            raise ReferenceAnalyzerError("영상 정보를 가져오지 못했습니다. URL을 확인하세요.")
        data = resp.json()
    return {
        "video_id": video_id,
        "url": canonical,
        "title": data.get("title", ""),
        "author_name": data.get("author_name", ""),
        "thumbnail_url": data.get("thumbnail_url"),
    }


def _guess_category(title: str, allowlist: list[str]) -> str:
    title_l = title.lower()
    if any(k in title for k in ("레시피", "요리", "먹", "음식", "food", "recipe")):
        return "food" if "food" in allowlist else allowlist[0]
    if any(k in title for k in ("고양이", "강아지", "반려", "pet", "cat", "dog")):
        return "daily_pet" if "daily_pet" in allowlist else allowlist[0]
    if any(k in title for k in ("팁", "꿀팁", "방법", "tip", "how")):
        return "tips" if "tips" in allowlist else allowlist[0]
    if "comedy" in allowlist or "코미디" in title_l:
        return "comedy" if "comedy" in allowlist else allowlist[0]
    return allowlist[0] if allowlist else "comedy"


def _keywords_from_title(title: str) -> list[str]:
    cleaned = re.sub(r"[#|\[\]()【】]", " ", title)
    parts = [p.strip() for p in re.split(r"[,·|/]", cleaned) if p.strip()]
    if not parts:
        return ["shorts", "참조", "리메이크"]
    return parts[:4]


def _rule_based_script(meta: dict[str, Any], category: str) -> dict[str, Any]:
    title = meta["title"] or "참조 Shorts"
    author = meta.get("author_name") or "크리에이터"
    hook = f"{title[:40]}… 스타일로 새로 풀어본다면?"
    keywords = _keywords_from_title(title)

    scenes = [
        {
            "seq": 1,
            "narration": hook,
            "visual_hint": "reference hook beat",
            "visual_prompt": (
                f"Vertical 9:16 YouTube Shorts, inspired by '{title}' style, "
                f"{category} mood, original footage, no watermark"
            ),
            "duration_sec": 8,
        },
        {
            "seq": 2,
            "narration": f"참고 영상의 핵심은 '{keywords[0]}' 포인트예요.",
            "visual_hint": "key message",
            "visual_prompt": f"Vertical short scene explaining {keywords[0]}, Korean audience",
            "duration_sec": 10,
        },
        {
            "seq": 3,
            "narration": "우리 채널 버전으로 바꿔보면 이렇게 흘러가요.",
            "visual_hint": "story beat",
            "visual_prompt": "Engaging vertical b-roll, lifestyle, photorealistic",
            "duration_sec": 10,
        },
        {
            "seq": 4,
            "narration": "마음에 들면 저장하고 구독해 주세요!",
            "visual_hint": "cta",
            "visual_prompt": "Clean CTA end card style vertical short",
            "duration_sec": 8,
        },
    ]
    duration = sum(s["duration_sec"] for s in scenes)
    return {
        "hook": hook,
        "scenes": scenes,
        "cta": "저장 & 구독!",
        "target_duration_sec": min(duration, 45),
        "forbidden_flags": ["no_verbatim_copy"],
        "reference": {
            "video_id": meta["video_id"],
            "url": meta["url"],
            "title": title,
            "author_name": author,
            "thumbnail_url": meta.get("thumbnail_url"),
            "style_notes": (
                f"'{title}' ({author}) 영상의 페이싱·훅 구조를 참고한 오리지널 대본입니다. "
                "원본 대사/영상을 그대로 복제하지 않습니다."
            ),
        },
    }


async def _openai_analyze_script(settings: Settings, meta: dict[str, Any], category: str) -> dict[str, Any] | None:
    if not settings.openai_api_key:
        return None
    prompt = (
        "You are a Korean YouTube Shorts producer. Given reference video metadata, "
        "create an ORIGINAL script inspired by structure/pacing only — never copy transcript. "
        "Return JSON: {hook, scenes:[{seq,narration,visual_hint,visual_prompt,duration_sec}], "
        "cta, target_duration_sec, style_notes}. "
        f"Category: {category}. Max 45 seconds total."
    )
    user = json.dumps(
        {
            "title": meta["title"],
            "author": meta.get("author_name"),
            "url": meta["url"],
        },
        ensure_ascii=False,
    )
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.5,
                },
            )
            if resp.status_code != 200:
                return None
            content = resp.json()["choices"][0]["message"]["content"]
            start = content.find("{")
            end = content.rfind("}") + 1
            if start < 0 or end <= start:
                return None
            parsed = json.loads(content[start:end])
            script = _rule_based_script(meta, category)
            script["hook"] = parsed.get("hook", script["hook"])
            script["cta"] = parsed.get("cta", script["cta"])
            if parsed.get("scenes"):
                script["scenes"] = parsed["scenes"]
            script["target_duration_sec"] = min(
                int(parsed.get("target_duration_sec", script["target_duration_sec"])), 45
            )
            script["reference"] = {
                "video_id": meta["video_id"],
                "url": meta["url"],
                "title": meta["title"],
                "author_name": meta.get("author_name"),
                "thumbnail_url": meta.get("thumbnail_url"),
                "style_notes": parsed.get("style_notes", "AI 분석 기반 오리지널 대본"),
            }
            return script
    except Exception:
        return None


async def analyze_reference_url(
    settings: Settings,
    url: str,
    category_allowlist: list[str],
) -> dict[str, Any]:
    meta = await fetch_video_metadata(url)
    category = _guess_category(meta["title"], category_allowlist)
    script = await _openai_analyze_script(settings, meta, category)
    if not script:
        script = _rule_based_script(meta, category)

    return {
        "video_id": meta["video_id"],
        "url": meta["url"],
        "title": meta["title"],
        "author_name": meta.get("author_name"),
        "thumbnail_url": meta.get("thumbnail_url"),
        "category": category,
        "hook_line": script["hook"],
        "keyword_cluster": _keywords_from_title(meta["title"]),
        "script": script,
        "style_notes": script.get("reference", {}).get("style_notes", ""),
    }


async def create_job_from_reference(
    session,
    channel,
    settings: Settings,
    url: str,
    analysis: dict[str, Any] | None = None,
):
    if analysis is None:
        analysis = await analyze_reference_url(settings, url, channel.category_allowlist)

    script = analysis["script"]
    code = await topic_code(session)
    topic = TopicCandidate(
        code=code,
        channel_id=channel.id,
        category=analysis["category"],
        keyword_cluster=analysis["keyword_cluster"],
        hook_line=analysis["hook_line"],
        score_view_potential=78.0,
        score_competition=55.0,
        score_production=40.0,
        score_copyright_safety=70.0,
        score_final=72.0,
        score_breakdown={
            "topic_source": "reference",
            "reference_url": analysis["url"],
            "reference_video_id": analysis["video_id"],
            "reference_title": analysis["title"],
            "reference_analysis": {
                "style_notes": analysis.get("style_notes"),
                "author_name": analysis.get("author_name"),
            },
        },
        status=TopicStatus.RECOMMENDED,
        source_links=[analysis["url"]],
        ai_label_required=True,
        copyright_risk=CopyrightRisk.LOW,
    )
    session.add(topic)
    await session.flush()

    job = await create_job_from_topic(session, topic, channel.operation_mode)
    job.script = Script(
        job_id=job.id,
        content=script,
        duration_estimate_sec=script.get("target_duration_sec", 38),
    )
    session.add(job.script)
    await session.flush()

    job_dir = Path(settings.data_dir) / "jobs" / job.code
    job_dir.mkdir(parents=True, exist_ok=True)
    ref_path = job_dir / "reference_analysis.json"
    ref_path.write_text(
        json.dumps(
            {
                "url": analysis["url"],
                "video_id": analysis["video_id"],
                "title": analysis["title"],
                "style_notes": analysis.get("style_notes"),
                "script_seed": True,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return topic, job, analysis
