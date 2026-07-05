"""ElevenLabs TTS — 캐릭터별 한국어·영어 음성."""

from __future__ import annotations

from pathlib import Path

import httpx

from app.config import Settings

ELEVENLABS_TTS = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


async def synthesize_speech(
    settings: Settings,
    text: str,
    voice_id: str,
    dest: Path,
    *,
    language: str = "ko",
) -> bool:
    api_key = getattr(settings, "elevenlabs_api_key", "")
    if not api_key or not voice_id or not text.strip():
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    body = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                ELEVENLABS_TTS.format(voice_id=voice_id),
                headers=headers,
                json=body,
            )
            if resp.status_code != 200:
                return False
            dest.write_bytes(resp.content)
            return dest.exists() and dest.stat().st_size > 0
    except Exception:
        return False


async def list_voices(settings: Settings) -> list[dict]:
    api_key = getattr(settings, "elevenlabs_api_key", "")
    if not api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": api_key},
            )
            if resp.status_code != 200:
                return []
            return [
                {"voice_id": v["voice_id"], "name": v.get("name", "")}
                for v in resp.json().get("voices", [])
            ]
    except Exception:
        return []
