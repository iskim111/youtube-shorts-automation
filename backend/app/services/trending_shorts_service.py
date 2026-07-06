"""Fetch a practical KR Shorts-like top list from the YouTube Data API."""

from __future__ import annotations

import json
import re
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings

_CACHE: dict[str, Any] = {"items": [], "fetched_at": 0.0}
YOUTUBE_SEARCH = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS = "https://www.googleapis.com/youtube/v3/videos"


def _parse_duration_seconds(value: str | None) -> int | None:
    if not value:
        return None

    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
    if not match:
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def _is_short_form(duration: str | None) -> bool:
    seconds = _parse_duration_seconds(duration)
    if seconds is None:
        return False
    return seconds <= 180


async def _search_candidate_ids(
    client: httpx.AsyncClient,
    api_key: str,
    *,
    limit: int,
    region: str,
    published_after: str | None,
    relevance_language: str | None,
) -> list[str]:
    video_ids: list[str] = []
    page_token: str | None = None

    while len(video_ids) < limit:
        params: dict[str, Any] = {
            "part": "snippet",
            "type": "video",
            "videoDuration": "short",
            "order": "viewCount",
            "regionCode": region,
            "maxResults": min(50, limit - len(video_ids)),
            "key": api_key,
        }
        if published_after:
            params["publishedAfter"] = published_after
        if relevance_language:
            params["relevanceLanguage"] = relevance_language
        if page_token:
            params["pageToken"] = page_token

        resp = await client.get(YOUTUBE_SEARCH, params=params)
        if resp.status_code != 200:
            raise ValueError(f"YouTube API error: {resp.text[:200]}")

        data = resp.json()
        for item in data.get("items", []):
            vid = item.get("id", {}).get("videoId")
            if vid and vid not in video_ids:
                video_ids.append(vid)

        page_token = data.get("nextPageToken")
        if not page_token or len(video_ids) >= limit:
            break

    return video_ids[:limit]


async def _fetch_video_details(
    client: httpx.AsyncClient,
    api_key: str,
    video_ids: list[str],
) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []

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

    return [item for item in details if _is_short_form(item.get("duration"))]


async def _fetch_most_popular_fallback(
    client: httpx.AsyncClient,
    api_key: str,
    *,
    limit: int,
    region: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page_token: str | None = None

    while len(items) < limit:
        resp = await client.get(
            YOUTUBE_VIDEOS,
            params={
                "part": "snippet,statistics,contentDetails",
                "chart": "mostPopular",
                "regionCode": region,
                "maxResults": 50,
                "pageToken": page_token,
                "key": api_key,
            },
        )
        if resp.status_code != 200:
            raise ValueError(f"YouTube API error: {resp.text[:200]}")

        data = resp.json()
        for item in data.get("items", []):
            duration = item.get("contentDetails", {}).get("duration")
            if not _is_short_form(duration):
                continue

            sn = item.get("snippet", {})
            st = item.get("statistics", {})
            items.append(
                {
                    "video_id": item["id"],
                    "url": f"https://www.youtube.com/shorts/{item['id']}",
                    "title": sn.get("title", ""),
                    "channel_title": sn.get("channelTitle", ""),
                    "thumbnail_url": (sn.get("thumbnails", {}).get("high") or {}).get("url"),
                    "view_count": int(st.get("viewCount", 0)),
                    "published_at": sn.get("publishedAt"),
                    "duration": duration,
                }
            )
            if len(items) >= limit:
                break

        page_token = data.get("nextPageToken")
        if not page_token or len(items) >= limit:
            break

    return items[:limit]


async def fetch_trending_shorts(settings: Settings, *, limit: int = 100, region: str = "KR") -> list[dict]:
    api_key = getattr(settings, "youtube_api_key", "")
    if not api_key:
        raise ValueError("YouTube Data API key is required. Set YOUTUBE_API_KEY in Settings.")

    ttl = settings.trending_cache_ttl_hours * 3600
    if _CACHE["items"] and time.time() - _CACHE["fetched_at"] < ttl:
        return _CACHE["items"][:limit]

    published_after = (datetime.now(UTC) - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")

    async with httpx.AsyncClient(timeout=30) as client:
        candidate_ids = await _search_candidate_ids(
            client,
            api_key,
            limit=limit,
            region=region,
            published_after=published_after,
            relevance_language="ko",
        )

        if not candidate_ids:
            candidate_ids = await _search_candidate_ids(
                client,
                api_key,
                limit=limit,
                region=region,
                published_after=None,
                relevance_language="ko",
            )

        if not candidate_ids:
            candidate_ids = await _search_candidate_ids(
                client,
                api_key,
                limit=limit,
                region=region,
                published_after=None,
                relevance_language=None,
            )

        details = await _fetch_video_details(client, api_key, candidate_ids)

        if not details:
            details = await _fetch_most_popular_fallback(client, api_key, limit=limit, region=region)

    details.sort(key=lambda x: x["view_count"], reverse=True)
    details = details[:limit]

    _CACHE["items"] = details
    _CACHE["fetched_at"] = time.time()

    cache_path = Path(settings.data_dir) / "cache" / "trending_shorts_kr.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8")

    return details
