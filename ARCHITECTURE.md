# ARCHITECTURE.md — ytdub

## 1. Overview

`ytdub` is a Python CLI (`yt-dlp` + system `ffmpeg`) that downloads one YouTube video
in a user-picked dub language and resolution, merging separate DASH streams into a single file.
Run: `pip install -e .` then `ytdub --url "URL" --lang ar --height 1080 --yes`, or `PYTHONPATH=src python -m ytdub`.
Entrypoints are the `ytdub` console script (`ytdub.cli:main` in `pyproject.toml`) and `src/ytdub/__main__.py`; both funnel into `cli._run`.

## 2. Folder structure

```
YouTube_Download_Dubbing/
├── pyproject.toml              # package `ytdub`, entry `ytdub.cli:main`, deps (yt-dlp/rich/click/questionary)
├── src/ytdub/
│   ├── __main__.py             # `python -m ytdub` shim → cli.main
│   ├── __init__.py             # version marker only
│   ├── cli.py                  # click options + config → update → URL → dub → quality → download orchestration (+ --history/--show-config/--reset-config)
│   ├── youtube.py              # ONLY yt-dlp layer: fetch_info / group_dubs / group_qualities / build_format
│   ├── downloader.py           # ensure_ffmpeg + single _attempt + download() outer retry loop resuming .part
│   ├── config.py               # first-run wizard + config.json load/save (app_dir)
│   ├── updater.py              # PyPI check + pip upgrade for yt-dlp/rich/click/questionary; never raises
│   ├── store.py                # SQLite history.db: pending/success/failed/resumed/retried + attempts
│   ├── ui.py                   # rich tables/prompts/progress; questionary with console-input fallback
│   ├── models.py               # dataclasses DubTrack / Quality / VideoInfo (no logic)
│   └── utils.py                # URL validation, language names, byte/duration formatting
├── tests/
│   ├── test_lang_grouping.py   # dub grouping against fixture
│   ├── test_format_builder.py  # quality grouping + format-string cases
│   ├── test_config_store.py    # config merge + store lifecycle + version compare + retry loop (stubbed _attempt)
│   └── fixtures/sample_info.json  # anonymized yt-dlp `formats` snapshot (offline tests)
├── docs/                       # 8 Arabic research notes feeding current boundaries (see docs/README.md)
├── downloads/                  # default output dir (git-ignored)
├── README.md / CONTRIBUTING.md / LICENSE / .gitignore
```

## 3. Dependency map

```
__main__.py → cli.py → config.py (stdlib only: json/os)
               │     → updater.py (stdlib only: urllib/subprocess/importlib.metadata)
               │     → store.py ──→ config.app_dir (path only, no cycle)
               │     → youtube.py ──→ models.py, utils.py + yt-dlp
               │     → downloader.py ──→ yt-dlp (no internal imports)
               │     → ui.py ──→ models.py, utils.py (leaf) + rich/questionary
               │     → utils.py (leaf, stdlib only)
tests/ → youtube.py + downloader._attempt (stubbed) + config/store (app_dir monkeypatched); never cli/network
```

Layer boundaries (enforced, see `AGENTS.md` / `CONTRIBUTING.md`):
`cli` (orchestration) → `youtube` (extraction) + `downloader` (side effects) + `ui` (rendering).
`models` and `utils` are leaves: imported by others, import nothing internal.
`youtube.py` and `downloader.py` each own one `yt-dlp` usage (inspect vs. download); neither imports the other.

## 4. Data flow

1. `cli._run` loads `config.ensure` (wizard on first interactive run, silent defaults under `--yes`), then `updater.run_startup_check` upgrades outdated tools (never raises; silent offline).
2. `cli._run` validates URL via `utils.is_youtube_url`, then `downloader.ensure_ffmpeg` fails fast if binary missing.
3. `youtube.fetch_info` extracts metadata without downloading; on ≤1 dub it retries once with `player-client android`.
4. `youtube.group_dubs` / `group_qualities` collapse raw `formats` into `DubTrack` / `Quality` lists for display.
5. `ui` shows video panel + dub/quality tables; `cli` resolves picks from flags (`--lang/--height/--yes/--keep-all-dubs/--audio-only`) or prompts.
6. `youtube.build_format` emits `(format_string, container, extra)` — `mp4`/`m4a` normally, `mkv` + multistreams for `--keep-all-dubs`.
7. `cli` opens a `store.record_start` row (pending), then `downloader.download` runs the outer retry loop (`max_retries` from config): each failed attempt records `retried` + sleeps, each rerun resumes the `.part` via `continuedl`; final state is `success` or `resumed` (attempts>1) or `failed`, reported as `(path, attempts, resumed)`.

Failures: bad URL / private-playlist-DRM / HTTP 429-PO-Token each abort with a short Arabic message (detail only under `--verbose`).

## 5. Architectural decisions

- All `yt-dlp` knowledge lives in `youtube.py` so format-string quirks and player-client workarounds change in one place.
- `downloader.py` takes a `progress_cb` and never imports `ui`, keeping side effects testable without a terminal.
- Plain dataclasses in `models.py` (instead of dicts) give the tables, prompts, and format builder a shared vocabulary.
- Tests run offline against `tests/fixtures/sample_info.json` because live YouTube responses are flaky and throttled.
- Default container is `mp4` for one dub (`m4a` for audio-only) and `mkv` for `--keep-all-dubs`, matching player support for multi-track files.
- Research stays in `docs/` (Arabic) and out of code comments so each module docstring points at the relevant note.
- Retry is an outer loop in `downloader.download` (not yt-dlp internals) so every attempt is observable: DB status, attempt count, and the `resumed` flag (attempt>1) are exact, not inferred.
- `config`/`store`/`updater` are stdlib-only infrastructure with no UI (except the wizard) and never raise into the main flow; tests redirect them via `config.app_dir` monkeypatching.

## 6. Where to change what

| Task | File |
|---|---|
| Add/change CLI flags or selection flow | `src/ytdub/cli.py` |
| Fix dub/quality detection or `-f` strings | `src/ytdub/youtube.py` + `tests/test_lang_grouping.py` / `tests/test_format_builder.py` |
| Change download, merge, retries, or ffmpeg check | `src/ytdub/downloader.py` |
| Change settings, wizard, or config keys | `src/ytdub/config.py` + `tests/test_config_store.py` |
| Change update check or package list | `src/ytdub/updater.py` (`PACKAGES`) |
| Change history schema or statuses | `src/ytdub/store.py` + `tests/test_config_store.py` |
| Change tables, prompts, progress layout | `src/ytdub/ui.py` |
| Add data carried between layers | `src/ytdub/models.py` |
| URL rules, language labels, formatting | `src/ytdub/utils.py` |
| New offline test data | `tests/fixtures/` (minimal anonymized JSON) |
| Design rationale lookup | `docs/` index at `docs/README.md` |
