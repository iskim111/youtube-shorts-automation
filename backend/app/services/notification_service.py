"""Slack / 로그 알림."""

from __future__ import annotations

import logging

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

EVENT_SEVERITY = {
    "quota.warning": "warning",
    "rights.hold": "warning",
    "upload.failed": "error",
    "upload.success": "info",
    "pipeline.failed": "error",
    "auto.publish": "info",
}


async def notify(settings: Settings, event: str, message: str, **extra) -> None:
    severity = EVENT_SEVERITY.get(event, "info")
    logger.info("[%s] %s %s", severity, event, message, extra=extra or None)

    if not settings.slack_webhook_url:
        return

    text = f"*[Shorts Automation]* `{event}`\n{message}"
    if extra:
        text += "\n" + "\n".join(f"• {k}: {v}" for k, v in extra.items())

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(settings.slack_webhook_url, json={"text": text})
    except Exception as exc:
        logger.warning("Slack notify failed: %s", exc)
