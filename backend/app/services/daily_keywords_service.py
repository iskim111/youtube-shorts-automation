"""일일 인기 검색어 — Google Trends RSS · 네이버 실시간 · 자동완성 확장 TOP 100."""

from __future__ import annotations

import json
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Literal

import httpx

from app.config import Settings

KeywordSource = Literal["google", "naver"]
KEYWORD_TARGET = 100

_CACHE: dict[str, Any] = {"items": None, "fetched_at": 0.0}
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

GOOGLE_RSS = "https://trends.google.com/trending/rss?geo=KR"
SIGNAL_REALTIME = "https://api.signal.bz/news/realtime"
GOOGLE_SUGGEST = "https://suggestqueries.google.com/complete/search"
NAVER_AC = "https://ac.search.naver.com/nx/ac"
HT_NS = "https://trends.google.com/trending/rss"


def _parse_google_rss(xml_text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = ET.fromstring(xml_text)
    for idx, item in enumerate(root.findall(".//item"), start=1):
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        traffic = item.findtext(f"{{{HT_NS}}}approx_traffic") or item.findtext("ht:approx_traffic")
        rows.append(
            {
                "rank": idx,
                "keyword": title,
                "source": "google",
                "traffic": (traffic or "").strip() or None,
            }
        )
    return rows


def _parse_signal_realtime(payload: dict) -> list[dict[str, Any]]:
    naver_rows: list[dict[str, Any]] = []
    top10 = payload.get("top10")

    if isinstance(top10, list):
        for item in top10:
            title = (item.get("keyword") or item.get("title") or "").strip()
            if not title:
                continue
            naver_rows.append(
                {
                    "rank": int(item.get("rank") or len(naver_rows) + 1),
                    "keyword": title,
                    "source": "naver",
                    "traffic": None,
                }
            )
        return naver_rows

    block = top10 if isinstance(top10, dict) else payload.get("data", {}).get("top10") or {}
    for idx, item in enumerate(block.get("issueNaver") or [], start=1):
        title = (item.get("title") or item.get("keyword") or "").strip()
        if title:
            naver_rows.append({"rank": idx, "keyword": title, "source": "naver", "traffic": None})
    return naver_rows


async def _fetch_google_suggest(client: httpx.AsyncClient, seed: str) -> list[str]:
    resp = await client.get(
        GOOGLE_SUGGEST,
        params={"client": "firefox", "q": seed, "hl": "ko", "gl": "kr"},
    )
    if resp.status_code != 200:
        return []
    try:
        data = json.loads(resp.text)
        return [str(s).strip() for s in data[1][:12] if str(s).strip()]
    except Exception:
        return []


async def _fetch_naver_suggest(client: httpx.AsyncClient, seed: str) -> list[str]:
    resp = await client.get(
        NAVER_AC,
        params={"q": seed, "q_enc": "utf-8", "st": 100, "frm": "nv", "r_format": "json"},
    )
    if resp.status_code != 200:
        return []
    try:
        items = resp.json().get("items", [[]])[0]
        out: list[str] = []
        for item in items[:12]:
            if isinstance(item, list) and item:
                out.append(str(item[0]).strip())
            elif isinstance(item, str):
                out.append(item.strip())
        return [k for k in out if k]
    except Exception:
        return []


def _expand_to_target(
    seeds: list[dict[str, Any]],
    extras: list[str],
    *,
    source: str,
    target: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    for seed in seeds:
        kw = seed["keyword"].strip()
        key = kw.lower()
        if kw and key not in seen:
            seen.add(key)
            rows.append(
                {
                    "rank": len(rows) + 1,
                    "keyword": kw,
                    "source": source,
                    "traffic": seed.get("traffic"),
                }
            )

    for kw in extras:
        if len(rows) >= target:
            break
        key = kw.lower()
        if not kw or key in seen:
            continue
        seen.add(key)
        rows.append({"rank": len(rows) + 1, "keyword": kw, "source": source, "traffic": None})

    return rows[:target]


def _fallback_keywords() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from app.data.trending_topics_ko import TRENDING_TOPIC_POOL

    pool = TRENDING_TOPIC_POOL * 10
    google = [
        {"rank": i + 1, "keyword": t.hook_line[:40], "source": "google", "traffic": None}
        for i, t in enumerate(pool[:KEYWORD_TARGET])
    ]
    naver = [
        {"rank": i + 1, "keyword": t.hook_line[:40], "source": "naver", "traffic": None}
        for i, t in enumerate(pool[:KEYWORD_TARGET])
    ]
    return google, naver


def _load_disk_cache(settings: Settings) -> dict[str, Any] | None:
    path = Path(settings.data_dir) / "cache" / "daily_keywords_kr.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("google") or data.get("naver"):
            return data
    except Exception:
        return None
    return None


async def _fetch_google_rss(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    resp = await client.get(GOOGLE_RSS)
    if resp.status_code != 200:
        return []
    return _parse_google_rss(resp.text)


async def _fetch_naver_realtime(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    resp = await client.get(SIGNAL_REALTIME)
    if resp.status_code != 200:
        return []
    return _parse_signal_realtime(resp.json())


async def _fetch_all_sources(settings: Settings, *, target: int = KEYWORD_TARGET) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    google_seeds: list[dict[str, Any]] = []
    naver_seeds: list[dict[str, Any]] = []
    google_extra: list[str] = []
    naver_extra: list[str] = []

    for verify in (True, False):
        try:
            async with httpx.AsyncClient(
                timeout=20,
                headers=_HEADERS,
                follow_redirects=True,
                verify=verify,
            ) as client:
                google_seeds = await _fetch_google_rss(client)
                naver_seeds = await _fetch_naver_realtime(client)

                seeds_for_google = [r["keyword"] for r in google_seeds[:20]]
                seeds_for_naver = [r["keyword"] for r in naver_seeds[:20]]
                all_seeds = list(dict.fromkeys(seeds_for_google + seeds_for_naver))[:25]

                for seed in all_seeds:
                    if len(google_extra) >= target:
                        break
                    google_extra.extend(await _fetch_google_suggest(client, seed))
                for seed in all_seeds:
                    if len(naver_extra) >= target:
                        break
                    naver_extra.extend(await _fetch_naver_suggest(client, seed))

            if google_seeds or naver_seeds:
                break
        except Exception:
            continue

    google = _expand_to_target(google_seeds, google_extra, source="google", target=target)
    naver = _expand_to_target(naver_seeds, naver_extra, source="naver", target=target)

    if not google and not naver:
        disk = _load_disk_cache(settings)
        if disk:
            google = disk.get("google", [])[:target]
            naver = disk.get("naver", [])[:target]

    if not google and not naver:
        google, naver = _fallback_keywords()

    return google, naver


async def fetch_daily_keywords(settings: Settings, *, limit: int = KEYWORD_TARGET) -> dict[str, Any]:
    """Google·네이버 인기 검색어 TOP N (기본 100)."""
    limit = min(max(limit, 1), KEYWORD_TARGET)
    ttl = max(settings.trending_cache_ttl_hours, 1) * 3600
    if _CACHE["items"] and time.time() - _CACHE["fetched_at"] < ttl:
        cached = _CACHE["items"]
        if cached.get("google") or cached.get("naver"):
            return {
                "google": cached.get("google", [])[:limit],
                "naver": cached.get("naver", [])[:limit],
                "combined": cached.get("combined", [])[: limit * 2],
                "fetched_at": cached.get("fetched_at"),
            }

    google, naver = await _fetch_all_sources(settings, target=limit)

    combined: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in google + naver:
        key = row["keyword"].lower()
        if key in seen:
            continue
        seen.add(key)
        combined.append({**row, "rank": len(combined) + 1})

    fetched_at = time.time()
    payload = {
        "google": google,
        "naver": naver,
        "combined": combined,
        "fetched_at": fetched_at,
    }
    _CACHE["items"] = payload
    _CACHE["fetched_at"] = fetched_at

    path = Path(settings.data_dir) / "cache" / "daily_keywords_kr.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "google": google[:limit],
        "naver": naver[:limit],
        "combined": combined[: limit * 2],
        "fetched_at": fetched_at,
    }
