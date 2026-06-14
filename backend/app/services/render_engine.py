"""FFmpeg 렌더 엔진 — 템플릿 3종 + 자막 burn-in."""

from __future__ import annotations

import subprocess
from pathlib import Path

from app.services.ffmpeg_path import ffmpeg_available, resolve_ffmpeg

RENDER_TEMPLATES = ("bold_center", "split_hook", "minimal_bottom")

_TEMPLATE_VF = {
    "bold_center": (
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        "drawtext=text='{hook}':fontsize=48:fontcolor=white:"
        "x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=black"
    ),
    "split_hook": (
        "scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,"
        "pad=1080:1920:0:960:color=0x1a1d27,"
        "drawtext=text='{hook}':fontsize=40:fontcolor=white:"
        "x=(w-text_w)/2:y=200:borderw=2:bordercolor=black"
    ),
    "minimal_bottom": (
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        "drawbox=x=0:y=h-200:w=1080:h=200:color=black@0.5:t=fill,"
        "drawtext=text='{hook}':fontsize=36:fontcolor=white:"
        "x=(w-text_w)/2:y=h-120:borderw=1:bordercolor=black"
    ),
}


def _safe(text: str) -> str:
    return text.replace("'", "").replace(":", " ").replace("\\", "")[:50]


def render_with_template(
    output_path: Path,
    hook_line: str,
    duration_sec: int,
    template: str = "bold_center",
    asset_path: Path | None = None,
    srt_path: Path | None = None,
) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    template = template if template in RENDER_TEMPLATES else "bold_center"
    hook = _safe(hook_line)

    if not ffmpeg_available():
        from app.services.render_stub import _write_minimal_mp4

        return _write_minimal_mp4(output_path, duration_sec)

    vf = _TEMPLATE_VF[template].format(hook=hook)

    if asset_path and asset_path.exists() and asset_path.stat().st_size > 0:
        input_args = ["-stream_loop", "-1", "-i", str(asset_path)]
    else:
        input_args = ["-f", "lavfi", "-i", f"color=c=0x1a1d27:s=1080x1920:d={duration_sec}"]

    ffmpeg_bin = resolve_ffmpeg() or "ffmpeg"
    cmd = [ffmpeg_bin, "-y", *input_args, "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={duration_sec}"]

    if srt_path and srt_path.exists():
        srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")
        vf = f"{vf},subtitles='{srt_escaped}'"

    cmd += [
        "-t",
        str(duration_sec),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    return result.returncode == 0 and output_path.exists()


def extract_thumbnail(video_path: Path, thumb_path: Path, at_sec: float = 1.0) -> bool:
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    if not ffmpeg_available() or not video_path.exists():
        return False
    ffmpeg_bin = resolve_ffmpeg() or "ffmpeg"
    cmd = [
        ffmpeg_bin,
        "-y",
        "-ss",
        str(at_sec),
        "-i",
        str(video_path),
        "-vframes",
        "1",
        "-q:v",
        "2",
        str(thumb_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0 and thumb_path.exists()
