#!/usr/bin/env python3
"""운영 준비 상태 점검 — FFmpeg, OAuth, 채널 연결."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import httpx


async def check(base_url: str) -> dict:
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        health = (await client.get("/health")).json()
        setup = (await client.get("/api/v1/setup/status")).json()
        return {"health": health, "setup": setup}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = asyncio.run(check(args.base_url))
    except httpx.ConnectError:
        print("API 미실행 — uvicorn app.main:app --port 8000", file=sys.stderr)
        return 1

    setup = result["setup"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=== Shorts Automation Setup ===")
        for c in setup["checks"]:
            mark = "OK" if c["ok"] else "!!"
            warn = " (주의)" if c.get("warning") else ""
            print(f"  [{mark}] {c['label']}: {c['detail']}{warn}")
        print()
        if setup["ready_for_real_upload"]:
            print("실제 업로드 준비 완료")
        else:
            print("실제 업로드 전 추가 설정 필요 (위 !! 항목 확인)")

    return 0 if setup["ready_for_real_upload"] or not args.json else 1


if __name__ == "__main__":
    raise SystemExit(main())
