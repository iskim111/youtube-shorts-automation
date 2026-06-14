"""스크립트 → SRT 자막 생성."""

from __future__ import annotations

from pathlib import Path


def _format_ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def script_to_srt(script: dict) -> str:
    lines: list[str] = []
    idx = 1
    t = 0.0
    for scene in script.get("scenes", []):
        duration = float(scene.get("duration_sec", 5))
        text = scene.get("narration", "")
        if not text:
            continue
        start = _format_ts(t)
        end = _format_ts(t + duration)
        lines.append(str(idx))
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")
        idx += 1
        t += duration
    return "\n".join(lines)


def write_srt(script: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(script_to_srt(script), encoding="utf-8")
    return output_path
