"""인기 검색어 기반 KR Shorts 수집 (YouTube Data API)."""

from __future__ import annotations

import json
import re
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.config import Settings
from app.services.daily_keywords_service import fetch_daily_keywords

_CACHE: dict[str, Any] = {"items": [], "keywords": [], "fetched_at": 0.0}
YOUTUBE_SEARCH = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS = "https://www.googleapis.com/youtube/v3/videos"
MAX_SHORT_SECONDS = 60


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
    return 0 < seconds <= MAX_SHORT_SECONDS


async def _search_by_query(
    client: httpx.AsyncClient,
    api_key: str,
    *,
    query: str,
    region: str,
    published_after: str | None,
    max_results: int = 15,
) -> list[str]:
    video_ids: list[str] = []
    params: dict[str, Any] = {
        "part": "snippet",
        "type": "video",
        "videoDuration": "short",
        "order": "viewCount",
        "q": query,
        "regionCode": region,
        "maxResults": min(50, max_results),
        "key": api_key,
    }
    if published_after:
        params["publishedAfter"] = published_after
    if "shorts" not in query.lower():
        params["q"] = f"{query} #shorts"

    resp = await client.get(YOUTUBE_SEARCH, params=params)
    if resp.status_code != 200:
        return video_ids

    for item in resp.json().get("items", []):
        vid = item.get("id", {}).get("videoId")
        if vid and vid not in video_ids:
            video_ids.append(vid)
    return video_ids


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
            duration = item.get("contentDetails", {}).get("duration")
            if not _is_short_form(duration):
                continue

            details.append(
                {
                    "video_id": item["id"],
                    "url": f"https://www.youtube.com/shorts/{item['id']}",
                    "title": sn.get("title", ""),
                    "channel_title": sn.get("channelTitle", ""),
                    "thumbnail_url": (sn.get("thumbnails", {}).get("high") or {}).get("url"),
                    "view_count": int(st.get("viewCount", 0)),
                    "published_at": sn.get("publishedAt"),
                    "duration": duration,
                    "matched_keyword": item.get("_matched_keyword"),
                    "keyword_source": item.get("_keyword_source"),
                }
            )

    return details


async def fetch_trending_shorts(
    settings: Settings,
    *,
    limit: int = 100,
    region: str = "KR",
    keyword: str | None = None,
) -> dict[str, Any]:
    api_key = getattr(settings, "youtube_api_key", "")
    if not api_key:
        raise ValueError("YouTube Data API 키가 필요합니다. Settings에서 YOUTUBE_API_KEY를 입력하세요.")

    cache_key = keyword or "__all__"
    ttl = settings.trending_cache_ttl_hours * 3600
    if (
        not keyword
        and _CACHE["items"]
        and time.time() - _CACHE["fetched_at"] < ttl
    ):
        return {
            "items": _CACHE["items"][:limit],
            "keywords": _CACHE.get("keywords", []),
            "count": min(limit, len(_CACHE["items"])),
            "region": region,
            "source": "daily_keywords",
        }

    keywords_data = await fetch_daily_keywords(settings, limit=100)
    google_kw = keywords_data.get("google", [])
    naver_kw = keywords_data.get("naver", [])
    all_keywords = keywords_data.get("combined", [])

    if keyword:
        search_keywords = [{"keyword": keyword, "source": "manual", "rank": 1}]
    else:
        search_keywords = all_keywords[:30]
        if not search_keywords:
            search_keywords = [{"keyword": "한국 쇼츠", "source": "fallback", "rank": 1}]

    published_after = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    video_ids: list[str] = []
    id_to_keyword: dict[str, dict[str, str]] = {}

    async with httpx.AsyncClient(timeout=30) as client:
        per_keyword = max(5, limit // max(len(search_keywords), 1) + 1)

        for kw_row in search_keywords:
            kw = kw_row["keyword"]
            ids = await _search_by_query(
                client,
                api_key,
                query=kw,
                region=region,
                published_after=published_after,
                max_results=per_keyword,
            )
            for vid in ids:
                if vid not in id_to_keyword:
                    id_to_keyword[vid] = {
                        "matched_keyword": kw,
                        "keyword_source": kw_row.get("source", "unknown"),
                    }
                if vid not in video_ids:
                    video_ids.append(vid)

        if len(video_ids) < limit // 2:
            for kw_row in search_keywords:
                ids = await _search_by_query(
                    client,
                    api_key,
                    query=kw_row["keyword"],
                    region=region,
                    published_after=None,
                    max_results=per_keyword,
                )
                for vid in ids:
                    if vid not in id_to_keyword:
                        id_to_keyword[vid] = {
                            "matched_keyword": kw_row["keyword"],
                            "keyword_source": kw_row.get("source", "unknown"),
                        }
                    if vid not in video_ids:
                        video_ids.append(vid)

        raw_details = await _fetch_video_details(client, api_key, video_ids[: limit * 2])
        for item in raw_details:
            meta = id_to_keyword.get(item["video_id"], {})
            item["matched_keyword"] = meta.get("matched_keyword")
            item["keyword_source"] = meta.get("keyword_source")

    raw_details.sort(key=lambda x: x["view_count"], reverse=True)
    items = raw_details[:limit]

    keyword_summary = {
        "google": google_kw,
        "naver": naver_kw,
        "combined": all_keywords,
    }

    if not keyword:
        _CACHE["items"] = items
        _CACHE["keywords"] = keyword_summary
        _CACHE["fetched_at"] = time.time()

        cache_path = Path(settings.data_dir) / "cache" / "trending_shorts_kr.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {"items": items, "keywords": keyword_summary},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    return {
        "items": items,
        "keywords": keyword_summary,
        "count": len(items),
        "region": region,
        "source": "daily_keywords" if not keyword else "keyword_search",
        "search_keyword": keyword,
    }
