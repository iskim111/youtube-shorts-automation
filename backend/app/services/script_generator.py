"""템플릿 기반 대본 생성 (파일럿)."""

from app.models.topic_candidate import TopicCandidate

CATEGORY_CTA = {
    "comedy": "공감되면 좋아요!",
    "food": "따라 해 보세요!",
    "daily_pet": "우리 아이도 그래요 ㅋㅋ",
    "tips": "도움 됐다면 저장!",
}

CATEGORY_VISUAL_BASE = {
    "comedy": "funny everyday moment in Korea",
    "food": "appetizing Korean food close-up",
    "daily_pet": "cute cat or dog in a cozy home",
    "tips": "modern smartphone lifestyle tip",
}


def _scene_visual_prompt(topic: TopicCandidate, narration: str, visual_hint: str) -> str:
    base = CATEGORY_VISUAL_BASE.get(topic.category, "vertical short video scene")
    hint = visual_hint.replace("_", " ")
    return (
        f"Vertical 9:16 YouTube Shorts scene, photorealistic, {base}. "
        f"Story: {narration}. Visual focus: {hint}. No text overlay, no watermark."
    )


def generate_script(topic: TopicCandidate) -> dict:
    hook = topic.hook_line
    keywords = " · ".join(topic.keyword_cluster[:3])
    cta = CATEGORY_CTA.get(topic.category, "좋아요 & 구독!")

    scene_defs = [
        (hook, f"{topic.category} hook", 8),
        (f"오늘의 키워드: {keywords}", "keyword overlay", 12),
        ("여러분은 어떤가요?", "reaction beat", 10),
        (cta, "cta end card", 8),
    ]

    scenes = []
    for seq, (narration, visual_hint, duration_sec) in enumerate(scene_defs, start=1):
        scenes.append(
            {
                "seq": seq,
                "narration": narration,
                "visual_hint": visual_hint,
                "visual_prompt": _scene_visual_prompt(topic, narration, visual_hint),
                "duration_sec": duration_sec,
            }
        )
    duration = sum(s["duration_sec"] for s in scenes)

    return {
        "hook": hook,
        "scenes": scenes,
        "cta": cta,
        "target_duration_sec": min(duration, 45),
        "forbidden_flags": [],
    }
