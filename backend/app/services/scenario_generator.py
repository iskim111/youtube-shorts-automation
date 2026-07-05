"""2인 대화·트렌드 주제 시나리오 생성."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import Settings
from app.models.character import Character

SERIES_PRESETS: dict[str, dict] = {
    "grandma_youth_en": {
        "label": "할머니 + 외국 청년 (한국어·영어)",
        "roles": ["grandmother", "youth"],
        "rules": (
            "한국어 일상 대화 3~4턴. 청년이 한 문장을 영어로 말하고 할머니가 쉬운 한국어로 설명. "
            "30~45초. 유머러스하고 따뜻한 톤."
        ),
    },
    "interview_ai": {
        "label": "AI 인터뷰 포맷",
        "roles": ["host", "guest"],
        "rules": "인터뷰 3~4문답. 훅은 질문형. 실존 유명인 이름 사용 금지.",
    },
}


async def generate_dialogue_scenario(
    settings: Settings,
    characters: list[Character],
    *,
    topic: str,
    reference_title: str | None = None,
    preset: str | None = None,
) -> dict[str, Any]:
    preset_rules = ""
    if preset and preset in SERIES_PRESETS:
        preset_rules = SERIES_PRESETS[preset]["rules"]

    char_desc = "\n".join(
        f"- {c.name} ({c.role}): voice={c.elevenlabs_voice_id}, style={c.speech_style}"
        for c in characters
    )

    if settings.openai_api_key:
        script = await _openai_dialogue(settings, topic, char_desc, preset_rules, reference_title)
        if script:
            return script

    return _fallback_dialogue(characters, topic, reference_title)


async def generate_trend_scenario(
    settings: Settings,
    *,
    video_title: str,
    channel_title: str,
    category: str = "comedy",
) -> dict[str, Any]:
    topic = f"인기 Shorts 주제: {video_title} (채널: {channel_title})"
    if settings.openai_api_key:
        prompt = (
            f"한국 유튜브 쇼츠용 오리지널 시나리오 JSON. 주제: {topic}. "
            "동일 주제지만 표현은 완전 새로. format=monologue 또는 dialogue. "
            "hook, scenes[{seq,narration,visual_hint,visual_prompt,duration_sec,character_role?}], "
            "cta, target_duration_sec, format. JSON만."
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
                    "temperature": 0.85,
                },
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    data = json.loads(content[start:end])
                    data.setdefault("format", "monologue")
                    data["source_topic"] = video_title
                    return data

    hook = f"{video_title[:35]}… 이렇게 풀어보면?"
    return {
        "format": "monologue",
        "hook": hook,
        "source_topic": video_title,
        "scenes": [
            {"seq": 1, "narration": hook, "visual_hint": "hook", "duration_sec": 8},
            {"seq": 2, "narration": "요즘 이 주제, 여러분은 어떻게 보세요?", "visual_hint": "talk", "duration_sec": 12},
            {"seq": 3, "narration": "저는 이렇게 생각해요.", "visual_hint": "point", "duration_sec": 10},
            {"seq": 4, "narration": "공감되면 저장!", "visual_hint": "cta", "duration_sec": 8},
        ],
        "cta": "저장 & 구독",
        "target_duration_sec": 38,
    }


async def _openai_dialogue(
    settings: Settings,
    topic: str,
    char_desc: str,
    preset_rules: str,
    reference_title: str | None,
) -> dict[str, Any] | None:
    ref = f"참고 포맷(복사 금지): {reference_title}" if reference_title else ""
    prompt = (
        "Korean YouTube Shorts dialogue script JSON.\n"
        f"Topic: {topic}\n{ref}\nCharacters:\n{char_desc}\nRules: {preset_rules}\n"
        "Output: {format:'dialogue', hook, scenes:[{seq,character_code,narration,language,visual_hint,duration_sec}], "
        "cta, target_duration_sec, characters:[{code,name,role}]}"
    )
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.9,
                },
            )
            if resp.status_code != 200:
                return None
            content = resp.json()["choices"][0]["message"]["content"]
            start = content.find("{")
            end = content.rfind("}") + 1
            if start < 0 or end <= start:
                return None
            return json.loads(content[start:end])
    except Exception:
        return None


def _fallback_dialogue(
    characters: list[Character],
    topic: str,
    reference_title: str | None,
) -> dict[str, Any]:
    a = characters[0] if characters else None
    b = characters[1] if len(characters) > 1 else a
    ac = a.code if a else "A"
    bc = b.code if b else "B"
    return {
        "format": "dialogue",
        "hook": topic[:50],
        "source_topic": reference_title or topic,
        "scenes": [
            {"seq": 1, "character_code": ac, "narration": "안녕, 오늘 뭐 배워볼까?", "language": "ko", "duration_sec": 6},
            {"seq": 2, "character_code": bc, "narration": "How are you today?", "language": "en", "duration_sec": 5},
            {"seq": 3, "character_code": ac, "narration": "How are you? 는 '잘 지내?'라는 뜻이야.", "language": "ko", "duration_sec": 10},
            {"seq": 4, "character_code": bc, "narration": "아, 그렇구나! Thanks!", "language": "ko", "duration_sec": 6},
            {"seq": 5, "character_code": ac, "narration": "다음 표현도 알려줄까?", "language": "ko", "duration_sec": 6},
        ],
        "cta": "구독하고 같이 공부해요",
        "target_duration_sec": 33,
    }
