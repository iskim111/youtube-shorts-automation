"""HeyGen AI 캐릭터 영상 생성."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings

HEYGEN_BASE = "https://api.heygen.com"


async def list_avatars(settings: Settings) -> list[dict]:
    api_key = getattr(settings, "heygen_api_key", "")
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{HEYGEN_BASE}/v2/avatars",
                headers={"X-Api-Key": api_key},
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            avatars = data.get("data", {}).get("avatars") or data.get("avatars") or []
            return [
                {
                    "avatar_id": a.get("avatar_id") or a.get("id"),
                    "name": a.get("avatar_name") or a.get("name", ""),
                }
                for a in avatars
                if a.get("avatar_id") or a.get("id")
            ]
    except Exception:
        return []


async def generate_avatar_video(
    settings: Settings,
    *,
    avatar_id: str,
    text: str,
    dest: Path,
    width: int = 1080,
    height: int = 1920,
) -> bool:
    """HeyGen v2 — 텍스트 기반 아바타 영상 (내장 TTS)."""
    api_key = getattr(settings, "heygen_api_key", "")
    if not api_key or not avatar_id or not text.strip():
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": text,
                    "voice_id": "",
                },
            }
        ],
        "dimension": {"width": width, "height": height},
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            create = await client.post(f"{HEYGEN_BASE}/v2/video/generate", headers=headers, json=payload)
            if create.status_code not in (200, 201):
                return False
            video_id = (create.json().get("data") or create.json()).get("video_id")
            if not video_id:
                return False

            video_url = await _poll_video_url(client, api_key, video_id)
            if not video_url:
                return False

            dl = await client.get(video_url, timeout=180)
            if dl.status_code != 200:
                return False
            dest.write_bytes(dl.content)
            return dest.exists() and dest.stat().st_size > 0
    except Exception:
        return False


async def _poll_video_url(client: httpx.AsyncClient, api_key: str, video_id: str) -> str | None:
    headers = {"X-Api-Key": api_key}
    for _ in range(60):
        resp = await client.get(f"{HEYGEN_BASE}/v1/video_status.get", params={"video_id": video_id}, headers=headers)
        if resp.status_code != 200:
            await asyncio.sleep(5)
            continue
        data = resp.json().get("data") or resp.json()
        status = data.get("status")
        if status == "completed":
            return data.get("video_url") or data.get("url")
        if status == "failed":
            return None
        await asyncio.sleep(5)
    return None
