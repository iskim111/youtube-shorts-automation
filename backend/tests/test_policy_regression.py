import json
import uuid
from pathlib import Path

import pytest

from app.models.enums import CopyrightRisk, TopicStatus
from app.models.topic_candidate import TopicCandidate
from app.services.rights_gate import check_rights
from app.services.topic_engine import compute_similarity_penalty

FIXTURES = Path(__file__).parent / "fixtures" / "policy_golden.json"


def _topic(data: dict) -> TopicCandidate:
    return TopicCandidate(
        code="T-TEST",
        channel_id=uuid.uuid4(),
        category=data.get("category", "comedy"),
        keyword_cluster=["test"],
        hook_line="test hook",
        copyright_risk=CopyrightRisk(data.get("copyright_risk", "low")),
        status=TopicStatus.GENERATED,
        ai_label_required=data.get("ai_label_required", False),
    )


@pytest.fixture
def golden_cases():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", json.loads(FIXTURES.read_text(encoding="utf-8")), ids=lambda c: c["id"])
def test_policy_golden(case):
    topic = _topic(case["topic"])
    expect = case["expect"]

    if "rights_passed" in expect:
        result = check_rights(topic)
        assert result["passed"] is expect["rights_passed"]

    if "ai_label_required" in expect:
        assert topic.ai_label_required is expect["ai_label_required"]

    if "similarity_penalty_min" in case:
        penalty = compute_similarity_penalty(case["hook"], case["similar_hooks"])
        assert penalty >= expect["similarity_penalty_min"]
