"""Pexels API — 무료 스톡 영상/이미지."""

from __future__ import annotations

import httpx

from app.config import Settings

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"


async def search_videos(settings: Settings, query: str, per_page: int = 3) -> list[dict]:
    if not settings.pexels_api_key:
        return []

    headers = {"Authorization": settings.pexels_api_key}
    params = {"query": query, "per_page": per_page, "orientation": "portrait"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(PEXELS_VIDEO_URL, headers=headers, params=params)
        if resp.status_code != 200:
            return []
        data = resp.json()

    results = []
    for video in data.get("videos", []):
        files = video.get("video_files", [])
        best = None
        for f in files:
            if f.get("width", 0) >= 720:
                best = f
                break
        if not best and files:
            best = files[0]
        if best:
            results.append(
                {
                    "source_type": "pexels",
                    "source_url": video.get("url", ""),
                    "download_url": best.get("link"),
                    "width": best.get("width"),
                    "height": best.get("height"),
                    "duration": video.get("duration"),
                    "photographer": video.get("user", {}).get("name", ""),
                    "license_status": "low",
                }
            )
    return results
