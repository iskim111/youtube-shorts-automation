"""YouTube 인기 Shorts TOP N 수집 (KR)."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings

_CACHE: dict[str, Any] = {"items": [], "fetched_at": 0.0}
YOUTUBE_SEARCH = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS = "https://www.googleapis.com/youtube/v3/videos"


async def fetch_trending_shorts(settings: Settings, *, limit: int = 100, region: str = "KR") -> list[dict]:
    api_key = getattr(settings, "youtube_api_key", "")
    if not api_key:
        raise ValueError("YouTube Data API 키가 필요합니다. Settings에서 YOUTUBE_API_KEY를 입력하세요.")

    ttl = settings.trending_cache_ttl_hours * 3600
    if _CACHE["items"] and time.time() - _CACHE["fetched_at"] < ttl:
        return _CACHE["items"][:limit]

    published_after = (datetime.now(UTC) - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
    video_ids: list[str] = []
    page_token: str | None = None

    async with httpx.AsyncClient(timeout=30) as client:
        while len(video_ids) < limit:
            params: dict[str, Any] = {
                "part": "snippet",
                "type": "video",
                "videoDuration": "short",
                "order": "viewCount",
                "regionCode": region,
                "relevanceLanguage": "ko",
                "publishedAfter": published_after,
                "maxResults": min(50, limit - len(video_ids)),
                "key": api_key,
            }
            if page_token:
                params["pageToken"] = page_token
            resp = await client.get(YOUTUBE_SEARCH, params=params)
            if resp.status_code != 200:
                raise ValueError(f"YouTube API 오류: {resp.text[:200]}")
            data = resp.json()
            for item in data.get("items", []):
                vid = item.get("id", {}).get("videoId")
                if vid:
                    video_ids.append(vid)
            page_token = data.get("nextPageToken")
            if not page_token or len(video_ids) >= limit:
                break

        video_ids = video_ids[:limit]
        details: list[dict] = []
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i : i + 50]
            vresp = await client.get(
                YOUTUBE_VIDEOS,
                params={
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(chunk),
                    "key": api_key,
                },
            )
            if vresp.status_code != 200:
                continue
            for item in vresp.json().get("items", []):
                sn = item.get("snippet", {})
                st = item.get("statistics", {})
                details.append(
                    {
                        "video_id": item["id"],
                        "url": f"https://www.youtube.com/shorts/{item['id']}",
                        "title": sn.get("title", ""),
                        "channel_title": sn.get("channelTitle", ""),
                        "thumbnail_url": (sn.get("thumbnails", {}).get("high") or {}).get("url"),
                        "view_count": int(st.get("viewCount", 0)),
                        "published_at": sn.get("publishedAt"),
                        "duration": item.get("contentDetails", {}).get("duration"),
                    }
                )

    details.sort(key=lambda x: x["view_count"], reverse=True)
    _CACHE["items"] = details
    _CACHE["fetched_at"] = time.time()

    cache_path = Path(settings.data_dir) / "cache" / "trending_shorts_kr.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8")

    return details[:limit]
