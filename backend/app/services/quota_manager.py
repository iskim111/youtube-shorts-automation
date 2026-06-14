"""YouTube API 쿼터 관리 (Redis 또는 인메모리 fallback)."""

from __future__ import annotations

from datetime import date

from app.config import Settings

# videos.insert 기본 일 100회
YOUTUBE_INSERT_DAILY_LIMIT = 100
YOUTUBE_UNITS_DAILY_LIMIT = 10000

_memory_counters: dict[str, int] = {}


def _key(prefix: str) -> str:
    return f"quota:{prefix}:{date.today().isoformat()}"


async def _incr(settings: Settings, key: str, amount: int = 1) -> int:
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        val = await client.incrby(key, amount)
        await client.expire(key, 86400 * 2)
        await client.aclose()
        return int(val)
    except Exception:
        _memory_counters[key] = _memory_counters.get(key, 0) + amount
        return _memory_counters[key]


async def _get(settings: Settings, key: str) -> int:
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        val = await client.get(key)
        await client.aclose()
        return int(val or 0)
    except Exception:
        return _memory_counters.get(key, 0)


async def record_upload(settings: Settings) -> int:
    return await _incr(settings, _key("youtube_insert"))


async def get_quota_status(settings: Settings) -> dict:
    insert_used = await _get(settings, _key("youtube_insert"))
    return {
        "youtube_insert_used": insert_used,
        "youtube_insert_limit": YOUTUBE_INSERT_DAILY_LIMIT,
        "youtube_insert_remaining": max(0, YOUTUBE_INSERT_DAILY_LIMIT - insert_used),
        "usage_percent": round(insert_used / YOUTUBE_INSERT_DAILY_LIMIT * 100, 1),
        "daily_upload_cap": settings.daily_upload_cap,
    }


async def can_upload(settings: Settings, channel_daily_count: int = 0) -> tuple[bool, str]:
    status = await get_quota_status(settings)
    if status["youtube_insert_remaining"] <= 0:
        return False, "YouTube insert 일일 쿼터 소진"
    if channel_daily_count >= settings.daily_upload_cap:
        return False, f"채널 일일 업로드 캡({settings.daily_upload_cap}) 초과"
    if status["usage_percent"] >= 80:
        from app.services.notification_service import notify

        await notify(settings, "quota.warning", "YouTube 쿼터 80% 도달", **status)
    return True, "ok"
