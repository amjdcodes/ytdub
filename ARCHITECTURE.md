# ARCHITECTURE.md — ytdub

> Generated from a full scan of this repo (no `app/` directory exists — the app lives in `src/ytdub/`). All paths below are relative to the project root `/root/YouTube_Download_Dubbing`.

## 1. Folder structure and role of each folder

```
YouTube_Download_Dubbing/
├── src/ytdub/              # THE app — all production code (importable as `ytdub.*`, needs PYTHONPATH=src unless `pip install -e .`)
│   ├── __init__.py         # Package marker + __version__ = "1.0.0"
│   ├── __main__.py         # Entry point for `python -m ytdub` → calls cli.main
│   ├── cli.py              # Entry point for `ytdub` console script + full URL→dub→quality→download flow
│   ├── youtube.py          # ONLY yt-dlp layer (fetch_info / group_dubs / group_qualities / build_format)
│   ├── downloader.py       # Download execution + ensure_ffmpeg (no rendering)
│   ├── ui.py               # ALL rendering (rich tables/prompts/progress)
│   ├── models.py           # Pure dataclasses (DubTrack / Quality / VideoInfo)
│   └── utils.py            # Pure helpers (URL validation, formatting, language names)
├── tests/                  # Offline pytest suite (never hits network)
│   ├── test_lang_grouping.py
│   ├── test_format_builder.py
│   └── fixtures/sample_info.json   # Anonymized yt-dlp `info_dict` (only `formats` used)
├── docs/                   # 8 Arabic research files + README — design rationale, NOT code
├── downloads/              # Default output dir for mp4/mkv/m4a (gitignored, never commit)
├── src/ytdub.egg-info/     # Build artifact from `pip install -e .` (gitignored)
├── .venv/ / __pycache__ / .pytest_cache/  # Local env/test caches (gitignored)
├── pyproject.toml          # Package metadata: name `ytdub`, requires-python >=3.10, deps yt-dlp/rich/click/questionary, script `ytdub = ytdub.cli:main`
├── opencode.json           # OpenCode agent config
├── CONTRIBUTING.md         # Mandatory layer rules + test/dependency policy
├── AGENTS.md               # Agent shortcut of the same rules + gotchas (ffmpeg binary, android fallback, --verbose)
├── README.md               # User docs (features, usage, troubleshooting, structure)
└── LICENSE                 # Unlicense (public domain)
```

| Folder | Role | Contains logic? |
|---|---|---|
| `src/ytdub/` | Production code, layered by file (see §2) | Yes — everything |
| `tests/` + `tests/fixtures/` | Offline verification of grouping + format strings | Test-only |
| `docs/` (`01`–`08` + `README.md`) | Research: dubbing mechanism, yt-dlp core, ffmpeg merging, CLI UX, blueprint, limits/legal, roadmap, sources | No code, reference only |
| `downloads/` | Runtime output (default `--output-dir`) | Generated media, gitignored |

## 2. Key files and what they do

### Entry points
- **`src/ytdub/__main__.py` (4 lines):** `from .cli import main; main()` — enables `python -m ytdub`. No logic.
- **`src/ytdub/__init__.py`:** Docstring + `__version__ = "1.0.0"` (consumed by `@click.version_option` in `cli.py`).
- **`src/ytdub/cli.py` (`main` + `_run`, ~159 lines):** Only orchestration + arg parsing (click).
  - `main(...)`: click options (`url`, `--url`, `--lang`, `--height`, `--yes`, `--output-dir`, `--player-client`, `--keep-all-dubs`, `--prefer-av1`, `--audio-only`, `--cookies`, `--cookies-from-browser`, `--verbose`, `--version`); wraps `_run` with `RuntimeError → red Arabic message + exit 1`, `KeyboardInterrupt → exit 130`; enables `rich_traceback` only if `--verbose`.
  - `_run(...)`: the 6-step flow (see §5). Owns: URL prompt/validation, `android` fallback refetch, dub/quality resolution (`--lang`/`--height`/`--yes` vs interactive), `build_format` call, `os.makedirs(output_dir)`, progress-hook closure, `download()` call, final `✅ تم:` line.

### Service / extraction layer
- **`src/ytdub/youtube.py`:** Sole owner of `yt-dlp` knowledge. Exports:
  - `fetch_info(url, player_client, cookies_file, cookies_from_browser, verbose) -> VideoInfo`: builds `YoutubeDL` opts (`skip_download=True`, `extractor_args.youtube.player_client`, `cookiefile`, `cookiesfrombrowser`), calls `extract_info(download=False)`, rejects playlists (`"entries" in info`), maps to `VideoInfo`. Converts `DownloadError` via `_friendly_error` (private→public Arabic: private/age-login, 429/bot-check, DRM, PO-Token/SABR).
  - `group_dubs(formats) -> list[DubTrack]`: filters `_is_audio_only` (`acodec != none`, `vcodec == none`), groups by `language` (split on `.`), classifies via `utils.classify_dub_kind`, picks `is_default` by `"original" in format_note`, best `abr/tbr`, sorts `original > dubbed > auto-dub > unknown > descriptive`, promotes single-track to `original/is_default`, assigns 1-based `index`.
  - `group_qualities(formats) -> list[Quality]`: filters `_is_video_only`, keeps best `tbr/vbr` (tie-break `filesize`), sorts heights desc, tags `1080p+avc → "موصى به ✅"`, `>=2160 or av01/vp09 → "يحتاج مشغلًا حديثًا"`, assigns 1-based `index`.
  - `build_format(dub, quality, keep_all_dubs, prefer_h264, audio_only) -> (fmt, container, extra)`: the only format-string builder. `audio_only → ba[language=X]/ba/b + m4a`; `keep_all_dubs → bv*+ba/b + mkv + {audio_multistreams: True}`; else `bv*[vcodec^=avc1][height<=H]+ba[language=X]/... + mp4 + {format_sort: [...]}` (or AV1-tolerant variant when `prefer_h264=False`).
  - Private: `_base_opts`, `_friendly_error`, `_is_audio_only`, `_is_video_only` — must stay in this file.

### Execution layer
- **`src/ytdub/downloader.py` (~83 lines):** Exports `ensure_ffmpeg(audio_only)` (fails fast with per-OS hint from `FFMPEG_INSTALL_HINT` if `shutil.which("ffmpeg")` is missing) and `download(url, fmt, container, outtmpl, sort, audio_multistreams, cookies_file, cookies_from_browser, verbose, progress_hook) -> str`. Builds `YoutubeDL` opts (`format`, `merge_output_format`, `outtmpl`, `format_sort`, `audio_multistreams`, `postprocessor_args ffmpeg -strict -2` for mp4), chains external `progress_hook` + internal `_hook` (captures `finished["path"]`), calls `ydl.download([url])`, resolves final path via `extract_info + prepare_filename` fallback. **No rich/questionary/console imports — by design.**

### Presentation layer
- **`src/ytdub/ui.py` (~127 lines):** Owns the shared `console = Console()` plus:
  - `show_video_info(info)`: `Panel` with title/uploader/duration/views.
  - `show_dubs_table(tracks)`: rich `Table` (#, اللغة, الكود, النوع via `KIND_AR`, الجودة `abr`); short-circuits to a yellow notice when ≤1 track.
  - `show_qualities_table(quals)`: rich `Table` (#, الدقة, FPS, الكودك, الحجم via `format_bytes`, ملاحظة) + hardcoded row `0 / صوت فقط 🎵 / m4a`.
  - `ask_dub(tracks) -> DubTrack`: `questionary.select` if available, else `ask_number` (Enter = default/original).
  - `ask_quality(quals) -> (Quality|None, audio_only: bool)`: same pattern; `len+1` / `0` = audio-only.
  - `ask_number(prompt, min, max, default)`, `_questionary_choices(items)`, `make_progress() -> Progress` (Spinner + Bar + %, Download, Speed, ETA columns).

### Data + helpers (leaf modules, no internal deps)
- **`src/ytdub/models.py`:** Three `@dataclass`es, zero imports from project: `DubTrack(index, lang, display, kind, is_default, abr, sample_format_id)`, `Quality(index, height, fps, vcodec, size_approx, sample_format_id, note)`, `VideoInfo(video_id, title, uploader, duration, view_count, formats, raw)`.
- **`src/ytdub/utils.py`:** Stdlib-only (`urllib.parse`): `LANG_NAMES` (17 codes incl. `und → غير محدد`), `YOUTUBE_HOSTS` allowlist, `is_youtube_url(url)` (scheme http/https + host match + `youtu.be` path check), `format_bytes`, `format_duration`, `lang_display`, `classify_dub_kind(note, raw) → original/dubbed/auto-dub/descriptive/unknown`, `KIND_AR` Arabic labels.

### Tests & fixtures
- **`tests/test_lang_grouping.py`:** `group_dubs` order `["ar","en","es"]`, `[0]` is `original+is_default`, `[2]` is `auto-dub`; single-lang promotes to original.
- **`tests/test_format_builder.py`:** qualities dedup/sort `[2160,1080,720]` + `موصى` note; `build_format(es,1080)` contains `language=es` + `height<=1080` + `mp4`; `keep_all → mkv + audio_multistreams`; `audio_only(ar) → ba[language=ar]...`.
- **`tests/fixtures/sample_info.json`:** Saved `{"formats": [...]}` fixture; tests read only the `formats` key — add new data here as minimal anonymized JSON, never live network.

### Config
- **`pyproject.toml`:** `requires-python >=3.10`, deps `yt-dlp[default]>=2024.8.6, rich>=13.7.0, click>=8.1.0, questionary>=2.0.0`; `[project.scripts] ytdub = ytdub.cli:main`; setuptools `where=["src"]`.

## 3. Dependency map (who calls who)

```
python -m ytdub ──→ __main__.py ──→ cli.main (click)
ytdub (console script) ───────────→ cli.main  [pyproject.toml]

cli._run
 ├── utils.is_youtube_url                    # step 1: validate
 ├── downloader.ensure_ffmpeg                # step 2: fail fast
 ├── youtube.fetch_info ──→ yt_dlp.YoutubeDL.extract_info
 │                          ├── models.VideoInfo (constructs)
 │                          └── utils (no — fetch itself is pure yt-dlp; classification happens downstream)
 ├── youtube.group_dubs ──→ utils.classify_dub_kind + utils.lang_display
 │                         └── models.DubTrack (constructs, sorted)
 ├── youtube.group_qualities ──→ models.Quality (constructs, sorted)
 ├── [retry] youtube.fetch_info(player_client="android")  # only if len(dubs)<=1 and no explicit --player-client
 ├── ui.show_video_info / show_dubs_table / show_qualities_table  # uses models + utils.format_* + KIND_AR
 ├── ui.ask_dub / ui.ask_quality ──→ questionary / rich console.input (fallback)
 ├── youtube.build_format(dub: DubTrack|None, quality: Quality|None) → (fmt, container, extra)
 └── downloader.download(fmt, container, ...) ──→ yt_dlp.YoutubeDL.download
      └── cli.hook closure ──→ ui.make_progress() task updates (progress_cb pattern)
```

Import graph (static):

| Importer | Imports from |
|---|---|
| `__main__.py` | `cli.main` |
| `cli.py` | `__init__.__version__`, `downloader.{download, ensure_ffmpeg}`, `ui.{ask_dub, ask_quality, console, make_progress, show_dubs_table, show_qualities_table, show_video_info}`, `utils.is_youtube_url`, `youtube.{build_format, fetch_info, group_dubs, group_qualities}` + external `click`, `rich.traceback` |
| `youtube.py` | `models.{DubTrack, Quality, VideoInfo}`, `utils.{classify_dub_kind, lang_display}` + external `yt_dlp` |
| `downloader.py` | external `yt_dlp` only (+ stdlib `platform`, `shutil`) — **no `ytdub.*` imports** |
| `ui.py` | `models.{DubTrack, Quality, VideoInfo}`, `utils.{KIND_AR, format_bytes, format_duration}` + external `rich`, `questionary` (lazy/optional) |
| `utils.py`, `models.py` | stdlib only — leaves of the graph, safe to import anywhere |
| `tests/*` | `youtube.{build_format, group_dubs, group_qualities}` + `fixtures/sample_info.json` |

External deps: `yt-dlp` (only touched in `youtube.py` + `downloader.py`), `rich` (only `cli.py` + `ui.py`), `click` (only `cli.py`), `questionary` (only `ui.py`, optional with `input()` fallback), `ffmpeg/ffprobe` system binaries (checked by `downloader.ensure_ffmpeg`, executed by yt-dlp post-merge).

## 4. Critical rules (what must never be modified directly / bypassed)

From `CONTRIBUTING.md` + `AGENTS.md` (mandatory layer boundaries):

1. **All yt-dlp logic stays in `youtube.py` — never leak it.** `fetch_info / group_dubs / group_qualities / build_format` and format-string/`extractor_args` knowledge must not appear in `cli.py`, `downloader.py`, `ui.py`, or `utils.py`. If you need a new format rule, edit `build_format` + add a test in `tests/test_format_builder.py`.
2. **No rendering in `downloader.py`.** It reports via the `progress_hook`/`progress_cb` callback only; tables, prompts, `console.print`, progress bars live in `ui.py`. Do not import `rich`/`questionary` there.
3. **Display code belongs in `ui.py` only.** New tables/prompts go there; `cli.py` only calls `show_*`/`ask_*`/`make_progress`.
4. **CLI flow belongs in `cli.py::_run`.** Arg parsing + URL→dub→quality→download orchestration stays there; do not move selection logic into `youtube.py` or download logic into `cli.py` beyond the existing `download()` call.
5. **`models.py` / `utils.py` are dependency-free helpers.** Do not add `yt_dlp`/`rich`/`click` imports to them; they must remain importable without third-party deps.
6. **Tests are offline and fixture-based — never add network calls to tests.** New grouping/format behavior requires a case in `tests/test_lang_grouping.py` / `tests/test_format_builder.py` with minimal anonymized JSON under `tests/fixtures/`.
7. **Keep `ensure_ffmpeg()` before any fetch** (`cli._run` step 2) and require the real system `ffmpeg`/`ffprobe` binaries — the PyPI `ffmpeg` package does not satisfy it.
8. **Do not bypass DRM/age-gates; do not commit secrets or media.** Never commit cookies, credentials, `.env`, `downloads/`, or `*.mp4/*.mkv/*.m4a/*.mp3` (see `.gitignore`). Stack is frozen (`yt-dlp`, `rich`, `click`, `questionary`) — new deps need PR justification.
9. **User-facing text is concise Arabic; technical detail behind `--verbose` only.** `docs/` (8 files) is the design reference — check the relevant file before changing dubbing/format/merge/error behavior.

Key invariants enforced by tests (do not break): `keep_all_dubs → container mkv + extra["audio_multistreams"] is True`; dub+quality format contains `language=<code>` and `height<=<h>`; audio-only format starts with `ba[language=...]` and container `m4a`.

## 5. Data flow: entry point → output

```
1. Entry: `ytdub [URL] [flags]` (console script → cli.main)  OR  `python -m ytdub ...` (__main__ → cli.main)
2. cli._run step 1 — URL: use argv URL or prompt `رابط الفيديو:` → utils.is_youtube_url rejects non-YouTube/truncated links (RuntimeError, Arabic).
3. cli._run step 2 — Gate: downloader.ensure_ffmpeg() raises with OS-specific install hint if binary missing.
4. cli._run step 3 — Fetch (no download): youtube.fetch_info(url, player_client, cookies…) → yt_dlp extract_info → models.VideoInfo(formats=[…]).
   Group: youtube.group_dubs(formats) → list[DubTrack]; youtube.group_qualities(formats) → list[Quality].
   Fallback: if len(dubs)<=1 and no explicit --player-client, refetch with player_client="android"; keep alt result only if it yields more dubs.
   Guard: no quals and not --audio-only → RuntimeError (private/deleted/DRM).
5. Present: ui.show_video_info → ui.show_dubs_table → ui.show_qualities_table (rich tables; single-dub case prints skip notice).
6. Resolve dub: --keep-all-dubs → dub=None | --lang X → exact match or RuntimeError listing available | --yes → is_default or [0] | else ui.ask_dub.
   Resolve quality: --keep-all-dubs → None | --height H → exact match or RuntimeError | --yes → 1080p or [0] | else ui.ask_quality → (Quality|None, audio_only).
7. Build: youtube.build_format(dub, quality, keep_all_dubs, prefer_h264=not prefer_av1, audio_only) → (fmt string, container mp4/mkv/m4a, extra{format_sort?, audio_multistreams?}).
8. Execute: makedirs(output_dir); outtmpl = <output_dir>/%(title).150B [%(id)s].%(ext)s; cli.hook closure maps yt-dlp progress dicts → ui.make_progress() task.
   downloader.download(url, fmt, container, outtmpl, sort=extra.format_sort, …) → yt-dlp downloads DASH parts + ffmpeg merges (mp4 single-dub / mkv multi / m4a audio-only; mp4 adds `-strict -2`).
9. Output: `✅ تم: ./downloads/<title> [<id>].<ext>  [<dub display|كل الدبلجات][<Hp|صوت فقط|الأفضل>][<container>]` (+ `format=… container=… sort=…` line first when --verbose).
```

Failure branches (all surfaced as concise Arabic `RuntimeError`, full traceback only with `--verbose`): unsupported URL, missing ffmpeg, playlist URL, empty info, no video qualities, unknown `--lang`/`--height`, private/login/age (`خاص أو محذوف…`), 429/bot-check (`جرّب لاحقًا أو --cookies-from-browser…`), DRM (`لا يمكن تحميله`), PO-Token/SABR (`حدّث yt-dlp إلى nightly وثبّت deno…`).
