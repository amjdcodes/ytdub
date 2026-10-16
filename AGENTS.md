# AGENTS.md — ytdub

Small Python CLI (`yt-dlp` + `ffmpeg`) that downloads a YouTube video in a chosen dub language + quality. `src/` layout, Python `>=3.10`, no CI/lint/typecheck — `pytest` is the only gate.

## Commands

```bash
pip install -e . pytest            # one-time setup
PYTHONPATH=src python -m pytest tests/ -q   # run all tests (offline, fixture-based)
PYTHONPATH=src python -m ytdub --help       # smoke check without install
```

- Always use `PYTHONPATH=src` unless the package is installed (`pip install -e .`); imports are `ytdub.*` under `src/ytdub/`.
- Entrypoints: `ytdub` (`ytdub.cli:main`) and `python -m ytdub` (`__main__.py`); flow starts in `cli.py::_run`.
- Non-interactive repro/verify: `ytdub --url "URL" --lang ar --height 1080 --yes`.

## Layer boundaries (mandatory, from CONTRIBUTING.md)

- `youtube.py` — the ONLY place for `yt-dlp` logic: `fetch_info` / `group_dubs` / `group_qualities` / `build_format`. Never leak format-string or extraction logic elsewhere.
- `downloader.py` — download + retry loop + `ensure_ffmpeg` only; reports via `progress_cb`, never renders. Rendering lives in `ui.py` (tables, prompts, progress bar).
- `cli.py` — arg parsing + config → update-check → URL → dub → quality → download flow only.
- `config.py` (`~/.config/ytdub/config.json` + first-run wizard), `updater.py` (PyPI check/upgrade, never raises), `store.py` (`history.db` statuses: pending/success/failed/resumed/retried) are infrastructure — no UI except the wizard.
- `models.py` (`DubTrack`/`Quality`/`VideoInfo`), `utils.py` (URL validation, language names) are helpers.

## Tests

- Offline only: `tests/` + `tests/fixtures/sample_info.json`. Never hit the network in tests.
- Any change to grouping or `build_format` needs a test in `tests/test_lang_grouping.py` / `tests/test_format_builder.py`; retry/DB/config changes go in `tests/test_config_store.py` (stub `downloader._attempt`, monkeypatch `config.app_dir`). New data goes in `tests/fixtures/` as minimal anonymized JSON.
- Key invariants: `keep_all_dubs` → `mkv` + `audio_multistreams=True`; dub+quality format contains `language=<code>` and `height<=<h>`; audio-only starts with `ba[language=...]`; `download(..., max_retries=N)` attempts exactly N+1 times and reports `(path, attempts, resumed)`.

## Gotchas

- `ffmpeg`/`ffprobe` must be the real system binaries (`apt`/`brew`/`choco`) — the PyPI package named `ffmpeg` does not count. `ensure_ffmpeg()` fails fast; keep it before any fetch.
- Missing dubs often means wrong player client, not no dubs: `cli.py` retries with `--player-client android`. `deno`/`node` + nightly `yt-dlp` needed for PO-Token/SABR cases.
- Stack is fixed (`yt-dlp`, `rich`, `click`, `questionary`) — don't add deps without PR justification. Full rationale lives in `docs/` (8 Arabic research files).
- User-facing messages are concise Arabic; technical detail goes behind `--verbose` only.
 - Never bypass DRM/age-gates; never commit cookies, credentials, `.env`, `downloads/`, or media files (`*.mp4/*.mkv/*.m4a/*.mp3` — see `.gitignore`).
- Config/DB live outside the repo (`~/.config/ytdub/`); in tests always monkeypatch `config.app_dir` to `tmp_path` so the real home dir is never touched.

<!-- architecture-pointer -->
## Project architecture
For project structure, layers, dependencies, data flow, or details
beyond this file, read `ARCHITECTURE.md` before exploring the codebase.
Do not scan the whole project when that file answers the question.
<!-- /architecture-pointer -->
