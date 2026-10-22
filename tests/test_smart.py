import json
from pathlib import Path

import pytest

import ytdub.cli as cli
import ytdub.config as config
import ytdub.preferences as preferences
import ytdub.store as store
from ytdub.autopick import PICK_CAPPED, PICK_EXACT, PICK_NONE, PICK_UPGRADED, find_dub, pick_quality
from ytdub.models import DubTrack, Quality


@pytest.fixture(autouse=True)
def _isolated_app_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "app_dir", lambda: str(tmp_path))
    yield


def test_smart_picks_defaults_to_off():
    assert config.DEFAULTS["smart_picks"] is False


def test_record_choice_and_preferred_counts():
    preferences.record_choice("ar", 1080)
    preferences.record_choice("ar", 1080)
    preferences.record_choice("en", 720)

    assert preferences.preferred_lang() == "ar"
    assert preferences.preferred_height() == 1080


def test_preferences_tie_is_broken_by_most_recent_choice():
    preferences.record_choice("ar", 1080)
    preferences.record_choice("en", 720)
    assert preferences.preferred_lang() == "en"
    assert preferences.preferred_height() == 720

    preferences.record_choice("ar", 1080)
    assert preferences.preferred_lang() == "ar"
    assert preferences.preferred_height() == 1080


def test_seed_fills_empty_preferences_only():
    preferences.seed({"ar": 3}, {"1080": 2}, "ar", 1080)
    assert preferences.preferred_lang() == "ar"
    assert preferences.preferred_height() == 1080

    preferences.seed({"en": 99}, {"720": 99}, "en", 720)
    assert preferences.preferred_lang() == "ar"
    assert preferences.preferred_height() == 1080


def test_corrupt_preferences_file_falls_back_to_empty():
    Path(config.app_dir()).mkdir(parents=True, exist_ok=True)
    Path(preferences.path()).write_text("{broken", encoding="utf-8")
    assert preferences.is_empty() is True
    preferences.record_choice("ar", 1080)
    assert preferences.preferred_lang() == "ar"


def test_find_dub_matches_language_code_case_insensitively():
    dubs = [DubTrack(1, "ar", "العربية", "dubbed"), DubTrack(2, "en", "English", "original")]
    assert find_dub(dubs, "AR").lang == "ar"
    assert find_dub(dubs, "es") is None
    assert find_dub(dubs, None) is None


def test_pick_quality_exact_upgraded_capped_and_missing():
    quals = [Quality(1, 720), Quality(2, 1080), Quality(3, 2160)]

    quality, kind = pick_quality(quals, 1080)
    assert (quality.height, kind) == (1080, PICK_EXACT)

    quality, kind = pick_quality(quals, 1440)
    assert (quality.height, kind) == (2160, PICK_UPGRADED)

    caps = [Quality(1, 720), Quality(2, 1080)]
    quality, kind = pick_quality(caps, 2160)
    assert (quality.height, kind) == (1080, PICK_CAPPED)

    assert pick_quality([], 1080) == (None, PICK_NONE)
    assert pick_quality(quals, None) == (None, PICK_NONE)


def test_store_selection_counts_ignore_failed_rows():
    first = store.record_start("https://youtu.be/a", lang="ar", height=1080)
    store.record_attempt(first, store.STATUS_SUCCESS)
    failed = store.record_start("https://youtu.be/b", lang="en", height=720)
    store.record_attempt(failed, store.STATUS_FAILED)
    store.record_skip("https://youtu.be/c", lang="ar", height=1080)

    langs, heights, last_lang, last_height = store.selection_counts()
    assert langs == {"ar": 2}
    assert heights == {"1080": 2}
    assert last_lang == "ar" and last_height == 1080


def test_cli_smart_flag_persists_and_seeds():
    from click.testing import CliRunner

    result = CliRunner().invoke(cli.main, ["--smart"])
    assert result.exit_code == 0
    saved = json.loads((Path(config.app_dir()) / "config.json").read_text(encoding="utf-8"))
    assert saved["smart_picks"] is True

    result = CliRunner().invoke(cli.main, ["--no-smart"])
    assert result.exit_code == 0
    saved = json.loads((Path(config.app_dir()) / "config.json").read_text(encoding="utf-8"))
    assert saved["smart_picks"] is False


def _fixture_info():
    from ytdub.models import VideoInfo

    raw = json.loads((Path(__file__).parent / "fixtures" / "sample_info.json").read_text(encoding="utf-8"))
    return VideoInfo(
        video_id=raw["id"],
        title=raw["title"],
        uploader="tester",
        duration=60,
        view_count=10,
        formats=raw["formats"],
        raw=raw,
    )


def _smart_cfg():
    return {
        "smart_picks": True,
        "skip_existing": True,
        "resume_on_failure": False,
        "max_retries": 0,
        "retry_wait_seconds": 1,
        "socket_timeout": 30,
        "concurrent_fragments": 4,
    }


def test_process_url_uses_smart_picks_without_recording_them(tmp_path, monkeypatch):
    info = _fixture_info()
    preferences.record_choice("ar", 1080)

    calls = []
    monkeypatch.setattr(cli, "fetch_info", lambda *a, **k: info)
    monkeypatch.setattr(cli, "ensure_ffmpeg", lambda *a, **k: None)
    monkeypatch.setattr(cli, "existing_output", lambda *a, **k: None)
    monkeypatch.setattr(cli.store, "record_start", lambda *a, **k: 1)
    monkeypatch.setattr(cli.store, "record_attempt", lambda *a, **k: None)

    def fake_download(*args, **kwargs):
        calls.append(args)
        return (str(tmp_path / "out.mp4"), 1, False)

    monkeypatch.setattr(cli, "download", fake_download)
    outdir = tmp_path / "downloads"

    cli._process_url(
        "https://youtu.be/x", _smart_cfg(), str(outdir), None, None, True, None,
        False, False, False, None, None, False, False,
    )

    assert len(calls) == 1
    fmt = calls[0][1]
    assert "language=ar" in fmt and "height<=1080" in fmt
    assert preferences.preferred_lang() == "ar"
    assert preferences.preferred_height() == 1080


def test_process_url_stops_when_learned_dub_is_missing(tmp_path, monkeypatch):
    info = _fixture_info()
    preferences.record_choice("fr", 1080)

    calls = []
    monkeypatch.setattr(cli, "fetch_info", lambda *a, **k: info)
    monkeypatch.setattr(cli, "ensure_ffmpeg", lambda *a, **k: None)
    monkeypatch.setattr(cli, "download", lambda *a, **k: calls.append(a))

    with pytest.raises(RuntimeError, match="fr"):
        cli._process_url(
            "https://youtu.be/x", _smart_cfg(), str(tmp_path / "downloads"), None, None, True, None,
            False, False, False, None, None, False, False,
        )

    assert calls == []
