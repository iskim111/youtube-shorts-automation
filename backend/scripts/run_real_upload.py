#!/usr/bin/env python3
"""실제 YouTube 비공개 업로드 파일럿 (OAuth 연결된 채널 사용)."""

from __future__ import annotations

import asyncio
import json
import sys

import httpx

DEFAULT_BASE = "http://127.0.0.1:8000"


async def run_real_upload(base_url: str) -> dict:
    async with httpx.AsyncClient(base_url=base_url, timeout=300.0) as client:
        setup = (await client.get("/api/v1/setup/status")).json()
        print(f"[setup] ready_for_real_upload={setup['ready_for_real_upload']}")
        if setup["ready_for_real_upload"] is not True:
            for check in setup["checks"]:
                if not check["ok"]:
                    print(f"  ! {check['id']}: {check['detail']}")

        channels = (await client.get("/api/v1/channels")).json()
        oauth_ch = next((c for c in channels if c.get("oauth_connected")), None)
        if not oauth_ch:
            raise RuntimeError("OAuth 연결된 채널이 없습니다. Settings에서 연결하세요.")

        channel_id = oauth_ch["id"]
        print(
            f"[channel] {oauth_ch['name']} "
            f"({oauth_ch.get('youtube_channel_title')}) {channel_id}"
        )

        topics = (await client.get("/api/v1/topics")).json()
        channel_topics = [
            t for t in topics if t.get("channel_id") == channel_id and t.get("status") != "rejected"
        ]
        if not channel_topics:
            channel_topics = (
                await client.post(
                    "/api/v1/topics/generate",
                    json={"channel_id": channel_id, "limit": 4},
                )
            ).json()
            print(f"[topics] generated {len(channel_topics)} candidates")

        topic = sorted(channel_topics, key=lambda t: t["scores"]["final"], reverse=True)[0]
        print(f"[topic] {topic['hook_line'][:80]}")

        approve = (await client.post(f"/api/v1/topics/{topic['id']}/approve")).json()
        job_id = approve["job_id"]
        print(f"[job] created {job_id}")

        run = (await client.post(f"/api/v1/jobs/{job_id}/run")).json()
        print(f"[pipeline] {run['status']}: {run.get('message', '')}")

        job = (await client.get(f"/api/v1/jobs/{job_id}")).json()
        print(f"[job] status={job['status']}")

        publish = (await client.post(f"/api/v1/jobs/{job_id}/publish")).json()
        print(f"[publish] {json.dumps(publish, ensure_ascii=False)}")

        return {"job_id": job_id, "publish": publish, "setup": setup}


def main() -> int:
    try:
        asyncio.run(run_real_upload(DEFAULT_BASE))
    except httpx.ConnectError:
        print(f"API 연결 실패: {DEFAULT_BASE}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"실업로드 실패: {exc}", file=sys.stderr)
        return 1
    print("[done] real upload pilot completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
