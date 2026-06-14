from app.services.subtitle_service import script_to_srt, write_srt


def test_script_to_srt_format():
    script = {
        "scenes": [
            {"narration": "첫 장면", "duration_sec": 5},
            {"narration": "둘째 장면", "duration_sec": 8},
        ]
    }
    srt = script_to_srt(script)
    assert "첫 장면" in srt
    assert "00:00:00,000 --> 00:00:05,000" in srt
    assert "00:00:05,000 --> 00:00:13,000" in srt


def test_write_srt_file(tmp_path):
    script = {"scenes": [{"narration": "테스트", "duration_sec": 3}]}
    path = write_srt(script, tmp_path / "sub.srt")
    assert path.exists()
    assert "테스트" in path.read_text(encoding="utf-8")
