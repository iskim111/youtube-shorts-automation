import uuid

from app.models.enums import CopyrightRisk, TopicStatus
from app.models.topic_candidate import TopicCandidate
from app.services.metadata_writer import build_metadata
from app.services.rights_gate import check_rights
from app.services.script_generator import generate_script


def _topic(**kwargs) -> TopicCandidate:
    return TopicCandidate(
        code=kwargs.get("code", "T-0001"),
        channel_id=kwargs.get("channel_id", uuid.uuid4()),
        category=kwargs.get("category", "comedy"),
        keyword_cluster=kwargs.get("keyword_cluster", ["직장인", "회식"]),
        hook_line=kwargs.get("hook_line", "회식 끝나고 꼭 나오는 그 한마디"),
        copyright_risk=kwargs.get("copyright_risk", CopyrightRisk.LOW),
        status=kwargs.get("status", TopicStatus.RECOMMENDED),
    )


def test_generate_script_has_scenes():
    script = generate_script(_topic())
    assert script["hook"]
    assert len(script["scenes"]) >= 3
    assert script["target_duration_sec"] <= 45


def test_build_metadata_includes_shorts():
    topic = _topic()
    script = generate_script(topic)
    meta = build_metadata(topic, script)
    assert "#shorts" in meta["title"]
    assert meta["ai_label_applied"] is True


def test_rights_gate_low_risk_passes():
    result = check_rights(_topic())
    assert result["passed"] is True


def test_rights_gate_high_risk_fails():
    result = check_rights(_topic(copyright_risk=CopyrightRisk.HIGH))
    assert result["passed"] is False
