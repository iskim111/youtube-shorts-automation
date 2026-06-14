"""템플릿 기반 대본 생성 (파일럿)."""

from app.models.topic_candidate import TopicCandidate

CATEGORY_CTA = {
    "comedy": "공감되면 좋아요!",
    "food": "따라 해 보세요!",
    "daily_pet": "우리 아이도 그래요 ㅋㅋ",
    "tips": "도움 됐다면 저장!",
}


def generate_script(topic: TopicCandidate) -> dict:
    hook = topic.hook_line
    keywords = " · ".join(topic.keyword_cluster[:3])
    cta = CATEGORY_CTA.get(topic.category, "좋아요 & 구독!")

    scenes = [
        {
            "seq": 1,
            "narration": hook,
            "visual_hint": f"{topic.category} hook",
            "duration_sec": 8,
        },
        {
            "seq": 2,
            "narration": f"오늘의 키워드: {keywords}",
            "visual_hint": "keyword overlay",
            "duration_sec": 12,
        },
        {
            "seq": 3,
            "narration": "여러분은 어떤가요?",
            "visual_hint": "reaction beat",
            "duration_sec": 10,
        },
        {
            "seq": 4,
            "narration": cta,
            "visual_hint": "cta end card",
            "duration_sec": 8,
        },
    ]
    duration = sum(s["duration_sec"] for s in scenes)

    return {
        "hook": hook,
        "scenes": scenes,
        "cta": cta,
        "target_duration_sec": min(duration, 45),
        "forbidden_flags": [],
    }
