# AGENTS.md — ytdub

Small Python CLI (`yt-dlp` + `ffmpeg`) that downloads a YouTube video in a chosen dub language + quality. `src/` layout, Python `>=3.10`, no CI/lint/typecheck — `pytest` is the only gate.

## Commands

```bash
pip install -e . pytest            # one-time setup
PYTHONPATH=src python -m pytest tests/ -q   # run all tests (offline, fixture-based)
PYTHONPATH=src python -m ytdub --help       # smoke check without install
```

- Always use `PYTHONPATH=src` unless the package is installed (`pip install -e .`); imports are `ytdub.*` under `src/ytdub/`.
- Entrypoints: `ytdub` (`ytdub.cli:main`) and `python -m ytdub` (`__main__.py`); flow starts in `cli.py::_run` (single URL) or `cli.py::_run_batch` (`--batch`), both feeding `cli.py::_process_url`.
- Non-interactive repro/verify: `ytdub --url "URL" --lang ar --height 1080 --yes`.
- Batch/replay verify: `ytdub --batch urls.txt --yes` and `ytdub --retry-last`.
- Interface language: `ytdub --ui-lang en` (persists to `config.json`); first run asks it first.

## Layer boundaries (mandatory, from CONTRIBUTING.md)

- `youtube.py` — the ONLY place for `yt-dlp` logic: `fetch_info` / `group_dubs` / `group_qualities` / `build_format` / `estimate_size`. Never leak format-string or extraction logic elsewhere.
- `downloader.py` — download + retry loop + `ensure_ffmpeg` only; reports via `progress_cb`, never renders. Rendering lives in `ui.py` (tables, prompts, progress bar).
- `cli.py` — arg parsing + orchestration only: `_setup` (config + cached update-check + output dir) then `_process_url` (URL → dub → quality → estimate → skip-existing → download); `--batch`/`--retry` reuse `_process_url`.
- `config.py` (`~/.config/ytdub/config.json` + first-run wizard), `updater.py` (PyPI check/upgrade with a timestamp cache in `state_dir`, never raises), `store.py` (`history.db` statuses: pending/success/failed/resumed/retried/skipped) are infrastructure — no UI except the wizard.
- `i18n.py` — the ONLY source of user-facing strings: `set_lang("ar"|"en")` + `t(key, **fmt)`, stdlib-only leaf. Never hardcode Arabic/English in other modules.
- `models.py` (`DubTrack`/`Quality`/`VideoInfo`), `utils.py` (URL validation, language names, `kind_label`, `existing_output`, `read_batch_file`, `retry_selection`) are helpers.

## Tests

- Offline only: `tests/` + `tests/fixtures/sample_info.json`. Never hit the network in tests.
- Any change to grouping or `build_format` needs a test in `tests/test_lang_grouping.py` / `tests/test_format_builder.py`; retry/DB/config changes go in `tests/test_config_store.py` (stub `downloader._attempt`, monkeypatch `config.app_dir`). Pure helpers (`existing_output` / `read_batch_file` / `retry_selection`) go in `tests/test_utils.py`. UI-language/message changes go in `tests/test_i18n.py` (which also asserts AR/EN key parity). New data goes in `tests/fixtures/` as minimal anonymized JSON.
- Key invariants: `keep_all_dubs` → `mkv` + `audio_multistreams=True`; dub+quality format contains `language=<code>` and `height<=<h>`; audio-only starts with `ba[language=...]`; `download(..., max_retries=N)` attempts exactly N+1 times and reports `(path, attempts, resumed)`; `estimate_size` sums video+audio and is `None` for `keep_all_dubs`; `existing_output` ignores `.part`/`.fNNN` fragments and matches the `[<id>].<container>` suffix; `--retry` maps `lang="all"`→`keep_all_dubs` and `container="m4a"`→`audio_only`; `updater._should_check` honours `update_check_interval_hours`; `config.ensure` on an existing config missing `ui_lang` asks only that question and preserves all other keys.

## Gotchas

- `ffmpeg`/`ffprobe` must be the real system binaries (`apt`/`brew`/`choco`) — the PyPI package named `ffmpeg` does not count. `ensure_ffmpeg()` fails fast; keep it before any fetch.
- Missing dubs often means wrong player client, not no dubs: `cli.py` retries with `--player-client android`. `deno`/`node` + nightly `yt-dlp` needed for PO-Token/SABR cases.
- Stack is fixed (`yt-dlp`, `rich`, `click`, `questionary`) — don't add deps without PR justification. Full rationale lives in `docs/` (8 Arabic research files).
- User-facing messages are concise and come only from `i18n.t(...)`; technical detail goes behind `--verbose` only.
- Any new AR message needs an EN twin (same key) or `tests/test_i18n.py` key-parity fails. Status/kind labels use `store.status_label` / `utils.kind_label`, never local dicts.
- Titles/paths contain `[<video_id>]`; wrap any interpolated string printed via `rich` in `rich.markup.escape()` or rich swallows the brackets as markup (`cli.py`, `ui.py`).
 - Never bypass DRM/age-gates; never commit cookies, credentials, `.env`, `downloads/`, or media files (`*.mp4/*.mkv/*.m4a/*.mp3` — see `.gitignore`).
- Config/DB live outside the repo (`~/.config/ytdub/`); in tests always monkeypatch `config.app_dir` to `tmp_path` so the real home dir is never touched. `store.py` calls `config.app_dir()` at runtime (module import) so the patch actually takes effect.

<!-- architecture-pointer -->
## Project architecture
For project structure, layers, dependencies, data flow, or details
beyond this file, read `ARCHITECTURE.md` before exploring the codebase.
Do not scan the whole project when that file answers the question.
<!-- /architecture-pointer -->
