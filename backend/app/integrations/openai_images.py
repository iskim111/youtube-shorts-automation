"""OpenAI Images API — 시나리오 맞춤 정지 이미지 생성 (유료, 선택)."""

from __future__ import annotations

from pathlib import Path

import httpx

from app.config import Settings

OPENAI_IMAGES_URL = "https://api.openai.com/v1/images/generations"


async def generate_scene_image(
    settings: Settings,
    prompt: str,
    dest: Path,
    *,
    size: str = "1024x1792",
) -> bool:
    if not settings.openai_api_key:
        return False

    body = {
        "model": "dall-e-3",
        "prompt": prompt[:4000],
        "n": 1,
        "size": size,
        "response_format": "url",
        "quality": "standard",
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(OPENAI_IMAGES_URL, headers=headers, json=body)
            if resp.status_code != 200:
                return False
            data = resp.json()
            items = data.get("data") or []
            if not items:
                return False
            image_url = items[0].get("url")
            if not image_url:
                return False
            img_resp = await client.get(image_url)
            if img_resp.status_code != 200:
                return False
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(img_resp.content)
            return dest.exists() and dest.stat().st_size > 0
    except Exception:
        return False
