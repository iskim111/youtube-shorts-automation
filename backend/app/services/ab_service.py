"""A/B 테스트 — 훅·템플릿 변형 할당."""

from __future__ import annotations

import hashlib

HOOK_VARIANTS = {
    "A": lambda hook: hook,
    "B": lambda hook: f"🔥 {hook}",
    "C": lambda hook: f"{hook} (공감 주의)",
}

TEMPLATE_VARIANTS = ["bold_center", "split_hook", "minimal_bottom"]


def assign_ab_variant(job_code: str) -> str:
    h = int(hashlib.md5(job_code.encode()).hexdigest(), 16)
    return ["A", "B", "C"][h % 3]


def apply_hook_variant(hook: str, variant: str) -> str:
    fn = HOOK_VARIANTS.get(variant, HOOK_VARIANTS["A"])
    return fn(hook)


def assign_template_variant(job_code: str) -> str:
    h = int(hashlib.md5(job_code.encode()).hexdigest(), 16)
    return TEMPLATE_VARIANTS[h % len(TEMPLATE_VARIANTS)]
