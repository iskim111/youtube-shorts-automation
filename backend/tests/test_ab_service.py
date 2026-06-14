from app.services.ab_service import apply_hook_variant, assign_ab_variant, assign_template_variant


def test_assign_ab_variant_deterministic():
    assert assign_ab_variant("J-0001") == assign_ab_variant("J-0001")
    assert assign_ab_variant("J-0001") in {"A", "B", "C"}


def test_apply_hook_variant_b():
    assert "🔥" in apply_hook_variant("테스트", "B")


def test_assign_template_variant():
    t = assign_template_variant("J-0001")
    assert t in {"bold_center", "split_hook", "minimal_bottom"}
