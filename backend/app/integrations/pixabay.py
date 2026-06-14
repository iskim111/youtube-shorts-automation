"""Pixabay API — 무료 스톡 영상."""

from __future__ import annotations

import httpx

from app.config import Settings

PIXABAY_VIDEO_URL = "https://pixabay.com/api/videos/"


async def search_videos(settings: Settings, query: str, per_page: int = 3) -> list[dict]:
    if not settings.pixabay_api_key:
        return []

    params = {
        "key": settings.pixabay_api_key,
        "q": query,
        "per_page": per_page,
        "video_type": "film",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(PIXABAY_VIDEO_URL, params=params)
        if resp.status_code != 200:
            return []
        data = resp.json()

    results = []
    for hit in data.get("hits", []):
        videos = hit.get("videos", {})
        medium = videos.get("medium") or videos.get("small") or videos.get("tiny")
        if medium:
            results.append(
                {
                    "source_type": "pixabay",
                    "source_url": hit.get("pageURL", ""),
                    "download_url": medium.get("url"),
                    "width": medium.get("width"),
                    "height": medium.get("height"),
                    "duration": hit.get("duration"),
                    "photographer": hit.get("user", ""),
                    "license_status": "low",
                }
            )
    return results
