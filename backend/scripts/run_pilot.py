#!/usr/bin/env python3
"""Semi-auto E2E 파일럿: topic → job → pipeline → publish(dry-run)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

DEFAULT_BASE = "http://localhost:8000"


async def run_pilot(base_url: str, topic_index: int) -> dict:
    async with httpx.AsyncClient(base_url=base_url, timeout=120.0) as client:
        health = (await client.get("/health")).json()
        print(f"[health] {health['status']} mode={health['operation_mode']}")

        channels = (await client.get("/api/v1/channels")).json()
        if not channels:
            created = (
                await client.post(
                    "/api/v1/channels",
                    json={"name": "파일럿 채널", "operation_mode": "semi_auto"},
                )
            ).json()
            channel_id = created["id"]
            print(f"[channel] created {channel_id}")
        else:
            channel_id = channels[0]["id"]
            print(f"[channel] using {channels[0]['name']} ({channel_id})")

        topics = (await client.get("/api/v1/topics")).json()
        if not topics:
            topics = (
                await client.post(
                    "/api/v1/topics/generate",
                    json={"channel_id": channel_id, "limit": 4},
                )
            ).json()
            print(f"[topics] generated {len(topics)} candidates")

        if not topics:
            raise RuntimeError("주제 후보가 없습니다.")

        idx = min(topic_index, len(topics) - 1)
        topic = topics[idx]
        print(f"[topic] pick #{idx}: {topic['hook_line'][:60]}… (score={topic['scores']['final']})")

        if topic["status"] not in ("recommended", "approved"):
            print(f"[topic] status={topic['status']} — 승인 시도")

        approve = (await client.post(f"/api/v1/topics/{topic['id']}/approve")).json()
        job_id = approve["job_id"]
        print(f"[job] created {job_id} status={approve['status']}")

        run = (await client.post(f"/api/v1/jobs/{job_id}/run")).json()
        print(f"[pipeline] {run['status']}: {run.get('message', '')}")

        job = (await client.get(f"/api/v1/jobs/{job_id}")).json()
        print(f"[job] final status={job['status']} stages={len(job['stages'])}")

        publish = (await client.post(f"/api/v1/jobs/{job_id}/publish")).json()
        print(
            f"[publish] status={publish['status']} dry_run={publish['dry_run']} "
            f"video_id={publish.get('youtube_video_id')}"
        )

        return {
            "health": health,
            "topic_id": topic["id"],
            "job_id": job_id,
            "job_status": job["status"],
            "publish": publish,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run semi-auto pilot against local API")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--topic-index", type=int, default=0)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    try:
        result = asyncio.run(run_pilot(args.base_url, args.topic_index))
    except httpx.ConnectError:
        print(f"API 연결 실패: {args.base_url} — uvicorn을 먼저 실행하세요.", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"파일럿 실패: {exc}", file=sys.stderr)
        return 1

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[done] wrote {args.json_out}")

    print("[done] pilot completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
