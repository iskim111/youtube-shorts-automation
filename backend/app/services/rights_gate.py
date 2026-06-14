"""권리·정책 게이트 (파일럿)."""

from app.models.enums import CopyrightRisk
from app.models.topic_candidate import TopicCandidate

HIGH_RISK_CATEGORIES = {"kpop", "sports_fandom"}


def check_rights(topic: TopicCandidate) -> dict:
    hold_reasons: list[str] = []

    if topic.copyright_risk == CopyrightRisk.HIGH:
        hold_reasons.append("copyright_risk_high")
    if topic.copyright_risk == CopyrightRisk.MEDIUM:
        hold_reasons.append("copyright_risk_medium_review")
    if topic.category in HIGH_RISK_CATEGORIES:
        hold_reasons.append("high_risk_category")

    if topic.copyright_risk == CopyrightRisk.HIGH:
        passed = False
    elif topic.copyright_risk == CopyrightRisk.MEDIUM:
        passed = "high_risk_category" not in hold_reasons
    else:
        passed = "high_risk_category" not in hold_reasons

    return {
        "passed": passed and topic.copyright_risk != CopyrightRisk.HIGH,
        "hold_reasons": hold_reasons,
        "ai_label_required": topic.ai_label_required,
    }
