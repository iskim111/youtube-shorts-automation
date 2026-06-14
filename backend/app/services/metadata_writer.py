"""업로드 메타데이터 생성."""

from app.models.topic_candidate import TopicCandidate

CATEGORY_TAGS = {
    "comedy": ["코미디", "공감", "직장인", "shorts"],
    "food": ["요리", "레시피", "간식", "shorts"],
    "daily_pet": ["반려동물", "고양이", "일상", "shorts"],
    "tips": ["생활팁", "꿀팁", "정보", "shorts"],
}


def build_metadata(topic: TopicCandidate, script: dict) -> dict:
    title = f"{topic.hook_line} #shorts"
    if len(title) > 100:
        title = title[:97] + "..."

    tags = CATEGORY_TAGS.get(topic.category, ["shorts", "쇼츠"])
    tags = list(dict.fromkeys(tags + topic.keyword_cluster[:3]))[:15]

    description = "\n".join(
        [
            topic.hook_line,
            "",
            "🤖 AI 보조 제작 콘텐츠",
            f"카테고리: {topic.category}",
            "",
            " ".join(f"#{t}" for t in tags[:5]),
        ]
    )

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "ai_label_applied": True,
    }
