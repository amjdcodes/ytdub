# ARCHITECTURE.md — ytdub

## 1. Overview

`ytdub` is a Python CLI (`yt-dlp` + system `ffmpeg`) that downloads one YouTube video
in a user-picked dub language and resolution, merging separate DASH streams into a single file.
It ships a bilingual Arabic/English interface with three responsive themes. Run: `pip install -e .` then `ytdub --url "URL" --lang ar --height 1080 --yes`, or `PYTHONPATH=src python -m ytdub`.
Entrypoints are the `ytdub` console script (`ytdub.cli:main` in `pyproject.toml`) and `src/ytdub/__main__.py`; both funnel into `cli.main`, which dispatches to `cli._run` (single URL), `cli._run_batch` (`--batch`) or `cli._retry_from_history` (`--retry`), all sharing `cli._process_url`.

## 2. Folder structure

```
ytdub/
├── pyproject.toml              # package `ytdub`, entry `ytdub.cli:main`, deps (yt-dlp/rich/click/questionary)
├── src/ytdub/
│   ├── __main__.py             # `python -m ytdub` shim → cli.main
│   ├── __init__.py             # version marker only
│   ├── cli.py                  # click options + setup/`_process_url` orchestration (+ --history/--batch/--retry/--overwrite/--show-config/--reset-config)
│   ├── youtube.py              # ONLY yt-dlp layer: fetch_info / group_dubs / group_qualities / build_format / estimate_size
│   ├── downloader.py           # ensure_ffmpeg + single _attempt + download() outer retry loop resuming .part
│   ├── config.py               # first-run wizard + config.json load/save (app_dir)
│   ├── updater.py              # PyPI check + pip upgrade for yt-dlp/rich/click/questionary; timestamped cache in state_dir; never raises
│   ├── store.py                # SQLite history.db: pending/success/failed/resumed/retried/skipped + attempts
│   ├── i18n.py                 # AR/EN message catalog: set_lang + t(key); stdlib-only leaf
│   ├── themes.py               # 3 UI palettes (classic/midnight/sand) + aliases/labels; data only
│   ├── ui.py                   # rich tables/prompts/estimate/progress; responsive layout + live theme switch
│   ├── models.py               # dataclasses DubTrack / Quality / VideoInfo (no logic)
│   └── utils.py                # URL validation, language names, kind_label, existing_output, read_batch_file, retry_selection
├── tests/
│   ├── test_lang_grouping.py   # dub grouping against fixture
│   ├── test_format_builder.py  # quality grouping + format-string cases + estimate_size
│   ├── test_config_store.py    # config merge + store lifecycle + version compare + retry loop (stubbed _attempt)
│   ├── test_i18n.py            # AR/EN key parity + language switch + ui_lang migration
│   ├── test_themes.py          # palette parity, theme switch, responsive breakpoints, preview
│   ├── test_utils.py           # existing_output / read_batch_file / retry_selection
│   └── fixtures/sample_info.json  # anonymized yt-dlp `formats` snapshot (offline tests)
├── docs/                       # 8 Arabic research notes feeding current boundaries (see docs/README.md)
├── downloads/                  # default output dir (git-ignored)
├── README.md / CONTRIBUTING.md / LICENSE / .gitignore
```

## 3. Dependency map

```
__main__.py → cli.py → config.py (stdlib: json/os) ──→ i18n.py, themes.py (labels only)
               │     → updater.py (stdlib: urllib/subprocess/importlib.metadata) ──→ i18n.py
               │     → store.py ──→ config.app_dir (path only) + i18n
               │     → youtube.py ──→ models.py, utils.py, i18n + yt-dlp
               │     → downloader.py ──→ yt-dlp + i18n (no other internal imports)
               │     → ui.py ──→ themes.py, models.py, utils.py, i18n (leaf) + rich/questionary
               │     → utils.py ──→ i18n (leaf, stdlib only)
               │     → i18n.py (leaf, stdlib only)
themes.py → i18n.py (labels/descriptions; no rich import)
tests/ → youtube.py + downloader._attempt (stubbed) + config/store (app_dir monkeypatched); never cli/network
```

Layer boundaries (enforced, see `AGENTS.md` / `CONTRIBUTING.md`):
`cli` (orchestration) → `youtube` (extraction) + `downloader` (side effects) + `ui` (rendering).
`models`, `utils`, and `i18n` are leaves: imported by others, import nothing internal.
`youtube.py` and `downloader.py` each own one `yt-dlp` usage (inspect vs. download); neither imports the other.
`store.py` reaches config through `config.app_dir()` at call time (not a bound import) so tests can patch it.
`i18n.py` holds every user-facing string; modules call `t(key, ...)` and never embed Arabic/English text.

## 4. Data flow

1. `cli._setup` calls `config.ensure`, which also selects the interface language: a fresh interactive install runs the wizard (language question first, then theme) and a fresh `--yes` run writes Arabic + classic defaults; an existing config missing `ui_lang` (older version) is asked **only** that question and merged without repeating the rest. `config.ensure` then calls `i18n.set_lang(cfg["ui_lang"])`, `cli._setup` calls `ui.set_theme(cfg["ui_theme"])`, and `updater.run_startup_check` upgrades outdated tools — throttled by a timestamp in `state_dir` (`update_check_interval_hours`), never raising and silent offline.
2. `cli._run` / `cli._run_batch` then call `downloader.ensure_ffmpeg` once (fails fast if the binary is missing). `--retry`/`--retry-last` skip setup concerns by reloading a stored row.
3. `cli._process_url` validates the URL via `utils.is_youtube_url`, then `youtube.fetch_info` extracts metadata without downloading; on ≤1 dub it retries once with `player-client android`.
4. `youtube.group_dubs` / `group_qualities` collapse raw `formats` into `DubTrack` / `Quality` lists (each carrying `size_approx`) for display.
5. `ui` shows video panel + dub/quality tables; `cli` resolves picks from flags (`--lang/--height/--yes/--keep-all-dubs/--audio-only`) or prompts.
6. `youtube.build_format` emits `(format_string, container, extra)` — `mp4`/`m4a` normally, `mkv` + multistreams for `--keep-all-dubs`. `youtube.estimate_size` reports the expected bytes and `ui.show_estimate` prints it.
7. `utils.existing_output` looks for a finished `[<id>].<container>` file in the output dir; if present, `skip_existing` (and no `--overwrite`) records a `skipped` row via `store.record_skip` and stops — otherwise a `store.record_start` row (pending) is opened.
8. `downloader.download` runs the outer retry loop (`max_retries` from config): each failed attempt records `retried` + sleeps, each rerun resumes the `.part` via `continuedl`; final state is `success` or `resumed` (attempts>1) or `failed`, reported as `(path, attempts, resumed)`.
9. `--batch` loops steps 3–8 over `utils.read_batch_file(FILE)` and prints a `succeeded • failed • total` summary (exit 1 if any failed). `--retry ID`/`--retry-last` rebuild the run from a `store.get`/`store.last_failed` row through `utils.retry_selection` (`lang="all"`→keep-all, `container="m4a"`→audio-only) and replay non-interactively.

Failures: bad URL / private-playlist-DRM / HTTP 429-PO-Token each abort with a short localized (AR/EN) message (detail only under `--verbose`).

## 5. Architectural decisions

- All `yt-dlp` knowledge lives in `youtube.py` so format-string quirks and player-client workarounds change in one place.
- `downloader.py` takes a `progress_cb` and never imports `ui`, keeping side effects testable without a terminal.
- Plain dataclasses in `models.py` (instead of dicts) give the tables, prompts, and format builder a shared vocabulary.
- Tests run offline against `tests/fixtures/sample_info.json` because live YouTube responses are flaky and throttled.
- Default container is `mp4` for one dub (`m4a` for audio-only) and `mkv` for `--keep-all-dubs`, matching player support for multi-track files.
- Research stays in `docs/` (Arabic) and out of code comments so each module docstring points at the relevant note.
- Retry is an outer loop in `downloader.download` (not yt-dlp internals) so every attempt is observable: DB status, attempt count, and the `resumed` flag (attempt>1) are exact, not inferred.
- `config`/`store`/`updater` are stdlib-only infrastructure with no UI (except the wizard) and never raise into the main flow; tests redirect them via `config.app_dir` monkeypatching (store resolves `config.app_dir()` at call time so the patch applies).
- The UI is bilingual through one flat catalog in `i18n.py`: `set_lang` normalizes `ar`/`en`, `t` falls back to Arabic then the key, and `tests/test_i18n.py` asserts AR/EN key parity so a missing translation fails CI. Status/kind labels are derived via `store.status_label`/`utils.kind_label`, not local dicts.
- `ui_lang` lives in `config.json`; the wizard asks it first and continues in that language. Migration reads the raw JSON (defaults are merged in `load`, so presence must come from `_read_raw`) and asks only the missing `ui_lang` question, leaving every other key untouched. `--ui-lang ar|en` persists a switch without re-running the wizard.
- `ui_theme` is data, not code: `themes.py` holds three palettes with identical semantic keys, `ui.py` builds one `rich.Theme` and swaps it on the shared `Console` (`push_theme`/`pop_theme`), so tables, prompts, banner, and progress all change together at runtime. `--theme` saves and applies; `--theme-menu` offers a live preview. Rendering code never hardcodes ANSI colors — only semantic style names (`primary`, `success`, `table.border`, ...).
- Layout responsiveness is computed in `ui.py` from `console.size.width`: `compact` (<62), `regular` (<96), `wide` (>=96), with `MAX_CONTENT_WIDTH=110` to keep long lines readable. Narrow layouts drop secondary columns (dub code, FPS, codec, note) while essentials stay; the preview uses the same functions as real runs.
- Sizing is derived from `filesize`/`filesize_approx` already present on the raw formats, kept in `models` (`Quality.size_approx`, `DubTrack.size_approx`) and summed by `youtube.estimate_size` — no extra network call.
- Skip-existing keys off the `[<video_id>]` token in the output filename (helpers in `utils.existing_output`), avoiding re-extraction to learn the final name; `--overwrite` / `skip_existing` decide the policy.
- `updater` stays decoupled from `config` by receiving `state_dir` as a parameter (cli passes `os.path.dirname(config_path())`), so the timestamp cache is testable without importing config.
- `--batch` and `--retry` are thin drivers over the same `_process_url`, so single-URL behavior and history replay never diverge; retry mapping is a pure helper (`utils.retry_selection`) rather than duplicated logic.
- Any path/title that can contain `[<id>]` is wrapped in `rich.markup.escape()` before printing (`cli.py`, `ui.py`), since rich would otherwise swallow the brackets.

## 6. Where to change what

| Task | File |
|---|---|
| Add/change CLI flags or selection flow | `src/ytdub/cli.py` |
| Batch mode / retry-from-history flow | `src/ytdub/cli.py` + `src/ytdub/utils.py` (`read_batch_file`, `retry_selection`) + `tests/test_utils.py` |
| Skip-existing policy or output matching | `src/ytdub/utils.py` (`existing_output`) + `src/ytdub/cli.py` + `tests/test_utils.py` |
| Size estimate | `src/ytdub/youtube.py` (`estimate_size`) + `src/ytdub/models.py` + `tests/test_format_builder.py` |
| Fix dub/quality detection or `-f` strings | `src/ytdub/youtube.py` + `tests/test_lang_grouping.py` / `tests/test_format_builder.py` |
| Change download, merge, retries, or ffmpeg check | `src/ytdub/downloader.py` |
| Change settings, wizard, or config keys | `src/ytdub/config.py` + `tests/test_config_store.py` |
| Interface language selection / `ui_lang` migration | `src/ytdub/config.py` + `src/ytdub/i18n.py` + `tests/test_i18n.py` |
| Add/change a theme or palette | `src/ytdub/themes.py` + `src/ytdub/ui.py` + `tests/test_themes.py` |
| Theme switching, banner, responsive breakpoints | `src/ytdub/ui.py` + `src/ytdub/cli.py` |
| Add/change any user-facing string | `src/ytdub/i18n.py` (both AR + EN) + `tests/test_i18n.py` |
| Status/kind label text | `src/ytdub/i18n.py` via `store.status_label` / `utils.kind_label` |
| Change update check, cache interval, or package list | `src/ytdub/updater.py` (`PACKAGES`, `_should_check`) + `tests/test_config_store.py` |
| Change history schema or statuses | `src/ytdub/store.py` + `tests/test_config_store.py` |
| Change tables, prompts, estimate/progress layout | `src/ytdub/ui.py` |
| Add data carried between layers | `src/ytdub/models.py` |
| URL rules, language labels, formatting, batch parsing | `src/ytdub/utils.py` |
| New offline test data | `tests/fixtures/` (minimal anonymized JSON) |
| Design rationale lookup | `docs/` index at `docs/README.md` |
