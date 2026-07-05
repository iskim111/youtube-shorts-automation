"""AI 캐릭터 모드 영상 합성 — 장면별 HeyGen + FFmpeg concat."""

from __future__ import annotations

import subprocess
from pathlib import Path

from app.config import Settings
from app.models.character import Character
from app.services.ffmpeg_path import resolve_ffmpeg
from app.services.heygen_service import generate_avatar_video
from app.services.tts_service import synthesize_speech


async def render_ai_character_video(
    settings: Settings,
    script: dict,
    characters_by_code: dict[str, Character],
    job_dir: Path,
    output_path: Path,
) -> bool:
    """dialogue 형식 시나리오 → 장면 클립 생성 → concat."""
    scenes = script.get("scenes") or []
    if not scenes:
        return False

    if not settings.heygen_configured:
        return False

    clips_dir = job_dir / "ai_clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    clip_paths: list[Path] = []

    for scene in scenes:
        seq = int(scene.get("seq", len(clip_paths) + 1))
        narration = scene.get("narration", "")
        char_code = scene.get("character_code")
        character = characters_by_code.get(char_code) if char_code else None
        avatar_id = character.heygen_avatar_id if character else ""
        if not avatar_id:
            first = next(iter(characters_by_code.values()), None)
            avatar_id = first.heygen_avatar_id if first else ""

        clip_path = clips_dir / f"scene_{seq}.mp4"
        ok = await generate_avatar_video(
            settings,
            avatar_id=avatar_id,
            text=narration,
            dest=clip_path,
        )
        if ok:
            clip_paths.append(clip_path)
        elif character and character.elevenlabs_voice_id:
            audio_path = clips_dir / f"scene_{seq}.mp3"
            if await synthesize_speech(
                settings,
                narration,
                character.elevenlabs_voice_id,
                audio_path,
                language=scene.get("language", "ko"),
            ):
                ok = _mux_audio_placeholder(clip_path, audio_path, int(scene.get("duration_sec", 8)))
                if ok:
                    clip_paths.append(clip_path)

    if not clip_paths:
        return False

    if len(clip_paths) == 1:
        output_path.write_bytes(clip_paths[0].read_bytes())
        return True

    return _concat_clips(clip_paths, output_path)


def _concat_clips(clips: list[Path], output: Path) -> bool:
    ffmpeg = resolve_ffmpeg() or "ffmpeg"
    list_file = output.parent / "_ai_concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in clips),
        encoding="utf-8",
    )
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c",
        "copy",
        str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return result.returncode == 0 and output.exists()


def _mux_audio_placeholder(video: Path, audio: Path, duration: int) -> bool:
    ffmpeg = resolve_ffmpeg() or "ffmpeg"
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x1a1d27:s=1080x1920:d={duration}",
        "-i",
        str(audio),
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-shortest",
        str(video),
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120).returncode == 0
