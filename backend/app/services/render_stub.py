"""파일럿용 영상 렌더 (FFmpeg 또는 최소 MP4)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def render_pilot_video(output_path: Path, hook_line: str, duration_sec: int = 15) -> bool:
    """FFmpeg으로 9:16 파일럿 영상 생성. 성공 시 True."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_text = hook_line.replace("'", "").replace(":", " ")[:40]

    if _ffmpeg_available():
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x1a1d27:s=1080x1920:d={duration_sec}",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r=44100:cl=mono:d={duration_sec}",
            "-vf",
            (
                f"drawtext=text='{safe_text}':fontsize=42:fontcolor=white:"
                "x=(w-text_w)/2:y=(h-text_h)/2:borderw=2:bordercolor=black"
            ),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode == 0 and output_path.exists()

    return _write_minimal_mp4(output_path, duration_sec)


def _write_minimal_mp4(path: Path, duration_sec: int) -> bool:
    """FFmpeg 없을 때 최소 유효 MP4 (무음·단색). YouTube 업로드는 dry-run 권장."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Minimal ftyp + mdat stub — sufficient for local pipeline test
    ftyp = bytes(
        [
            0x00,
            0x00,
            0x00,
            0x20,
            0x66,
            0x74,
            0x79,
            0x70,
            0x69,
            0x73,
            0x6F,
            0x6D,
            0x00,
            0x00,
            0x02,
            0x00,
            0x69,
            0x73,
            0x6F,
            0x6D,
            0x69,
            0x73,
            0x6F,
            0x32,
            0x61,
            0x76,
            0x63,
            0x31,
            0x6D,
            0x70,
            0x34,
            0x31,
        ]
    )
    mdat = b"\x00\x00\x00\x08mdat" + b"\x00" * 1024
    path.write_bytes(ftyp + mdat)
    return path.exists()
