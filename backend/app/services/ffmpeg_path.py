"""FFmpeg 실행 파일 경로 해석 — PATH, FFMPEG_PATH, 프로젝트 tools/ 순."""

from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path


def _project_tools_ffmpeg() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "tools" / "ffmpeg" / "ffmpeg.exe"
        if candidate.exists():
            return candidate
        candidate = parent / "tools" / "ffmpeg" / "ffmpeg"
        if candidate.exists():
            return candidate
    return None


@lru_cache
def resolve_ffmpeg() -> str | None:
    from app.config import get_settings

    settings_path = get_settings().ffmpeg_path.strip()
    if settings_path and Path(settings_path).exists():
        return settings_path

    env = os.environ.get("FFMPEG_PATH", "").strip()
    if env and Path(env).exists():
        return env

    which = shutil.which("ffmpeg")
    if which:
        return which

    bundled = _project_tools_ffmpeg()
    return str(bundled) if bundled else None


def ffmpeg_available() -> bool:
    return resolve_ffmpeg() is not None


def ffmpeg_version() -> str | None:
    binary = resolve_ffmpeg()
    if not binary:
        return None
    try:
        result = subprocess.run(
            [binary, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout.splitlines()[0]
    except Exception:
        return None
    return None
