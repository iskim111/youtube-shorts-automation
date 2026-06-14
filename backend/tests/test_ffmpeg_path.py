from pathlib import Path

from app.services.ffmpeg_path import ffmpeg_available, resolve_ffmpeg


def test_resolve_project_ffmpeg():
    path = resolve_ffmpeg()
    if path:
        assert Path(path).exists()
        assert ffmpeg_available()
    else:
        assert not ffmpeg_available()
