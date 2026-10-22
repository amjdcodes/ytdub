import json

import ytdub.config as config
import ytdub.store as store
from ytdub.updater import _parse_version


def test_defaults_cover_retry_and_update_keys():
    for key in ("resume_on_failure", "max_retries", "retry_wait_seconds", "auto_update_check", "auto_update_install", "output_dir"):
        assert key in config.DEFAULTS


def test_load_merges_missing_keys(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "ytdub"
    cfg_dir.mkdir()
    (cfg_dir / "config.json").write_text(json.dumps({"max_retries": 3}), encoding="utf-8")
    monkeypatch.setattr(config, "app_dir", lambda: str(cfg_dir))
    cfg, exists = config.load()
    assert exists is True
    assert cfg["max_retries"] == 3
    assert cfg["retry_wait_seconds"] == config.DEFAULTS["retry_wait_seconds"]


def test_store_lifecycle(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "ytdub"
    monkeypatch.setattr(config, "app_dir", lambda: str(cfg_dir))
    row = store.record_start("https://youtu.be/x", video_id="x", title="T", lang="ar", height=1080)
    store.record_attempt(row, store.STATUS_RETRIED, error="net down")
    store.record_attempt(row, store.STATUS_RESUMED, filepath="/tmp/f.mp4")
    rows = store.recent(5)
    assert rows[0]["status"] == store.STATUS_RESUMED
    assert rows[0]["attempts"] == 2
    assert rows[0]["filepath"] == "/tmp/f.mp4"


def test_version_compare():
    assert _parse_version("2025.10.1") > _parse_version("2024.8.6")
    assert not (_parse_version("2024.8.6") > _parse_version("2025.10.1"))


def test_download_retries_then_resumes(monkeypatch):
    import ytdub.downloader as dl

    calls = []

    def fake_attempt(*a, **k):
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("net down")
        return "/tmp/f.mp4"

    monkeypatch.setattr(dl, "_attempt", fake_attempt)
    monkeypatch.setattr(dl.time, "sleep", lambda s: None)
    seen = []
    path, attempts, resumed = dl.download(
        "https://youtu.be/x", "b", "mp4", "/tmp/%(id)s.%(ext)s",
        max_retries=5, retry_wait=1, on_attempt=lambda n, ok, e: seen.append((n, ok)),
    )
    assert (path, attempts, resumed) == ("/tmp/f.mp4", 3, True)
    assert seen == [(1, False), (2, False), (3, True)]


def test_download_gives_up(monkeypatch):
    import ytdub.downloader as dl
    from ytdub import i18n

    i18n.set_lang("ar")
    monkeypatch.setattr(dl, "_attempt", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("dead")))
    monkeypatch.setattr(dl.time, "sleep", lambda s: None)
    try:
        dl.download("https://youtu.be/x", "b", "mp4", "/tmp/x", max_retries=2, retry_wait=1)
        raise AssertionError("should have raised")
    except RuntimeError as e:
        assert "بعد 3 محاولات" in str(e)


def test_new_infra_defaults_present():
    for key in ("skip_existing", "update_check_interval_hours", "ui_lang", "smart_picks"):
        assert key in config.DEFAULTS


def test_store_get_skip_and_last_failed(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "ytdub"
    monkeypatch.setattr(config, "app_dir", lambda: str(cfg_dir))
    row = store.record_start("https://youtu.be/a", video_id="a", title="T", lang="ar", height=1080)
    store.record_attempt(row, store.STATUS_FAILED, error="boom")
    got = store.get(row)
    assert got["status"] == store.STATUS_FAILED and got["attempts"] == 1
    assert got["url"] == "https://youtu.be/a"
    assert store.last_failed()["id"] == row
    assert store.get(999999) is None

    kid = store.record_skip("https://youtu.be/b", video_id="b", title="B", lang="en", height=720, container="mp4", filepath="/tmp/b.mp4")
    skip = store.get(kid)
    assert skip["status"] == store.STATUS_SKIPPED
    assert skip["attempts"] == 0
    assert skip["filepath"] == "/tmp/b.mp4"


def test_update_check_interval_cache(tmp_path):
    from ytdub import updater

    d = str(tmp_path)
    assert updater._should_check(d, 24) is True
    updater._touch_stamp(d)
    assert updater._should_check(d, 24) is False
    assert updater._should_check(d, 0) is True
    assert updater._should_check(None, 24) is True
