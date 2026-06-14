from app.models.enums import CopyrightRisk, TopicStatus
from app.services.topic_engine import (
    compute_final_score,
    compute_similarity_penalty,
    filter_by_allowlist,
    hook_similarity,
    resolve_status,
    score_template,
    TOPIC_TEMPLATES,
)


def test_compute_final_score_weights():
    score = compute_final_score(
        view_potential=80,
        competition=50,
        production=20,
        copyright_safety=90,
    )
    expected = 80 * 0.4 + (100 - 50) * 0.25 + (100 - 20) * 0.2 + 90 * 0.15
    assert score == round(expected, 1)


def test_similarity_penalty_applied():
    penalty = compute_similarity_penalty(
        "회식 끝나고 꼭 나오는 그 한마디",
        ["회식 끝나고 꼭 나오는 그 한마디"],
    )
    assert penalty >= 10


def test_hook_similarity_identical():
    assert hook_similarity("a b c", "a b c") == 1.0


def test_filter_by_allowlist():
    filtered = filter_by_allowlist(TOPIC_TEMPLATES, ["comedy", "food"])
    assert all(t.category in {"comedy", "food"} for t in filtered)
    assert len(filtered) >= 2


def test_resolve_status_high_copyright():
    status = resolve_status(CopyrightRisk.HIGH, 0, 0, "comedy", 90)
    assert status == TopicStatus.REVIEW_REQUIRED


def test_resolve_status_recommended():
    status = resolve_status(CopyrightRisk.LOW, 0, 0, "comedy", 79.3)
    assert status == TopicStatus.RECOMMENDED


def test_score_template_returns_final():
    template = TOPIC_TEMPLATES[0]
    result = score_template(template, [])
    assert "final_score" in result
    assert result["final_score"] > 0
    assert result["status"] in TopicStatus
