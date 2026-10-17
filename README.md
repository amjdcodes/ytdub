![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![yt-dlp](https://img.shields.io/badge/yt--dlp-core-red)
![FFmpeg](https://img.shields.io/badge/FFmpeg-required-green?logo=ffmpeg)
![License](https://img.shields.io/badge/License-Unlicense-yellow)

# ytdub

> **A Python CLI that downloads a YouTube video with the dubbing language and quality you pick from two tidy tables.**

[What It Does](#what-it-does) · [Quick Start](#quick-start) · [Usage](#usage) · [Configuration](#configuration) · [Architecture](#architecture) · [Troubleshooting](#troubleshooting) · [Contributing](#contributing)

---

## What It Does

The dubbing problem on YouTube: a single video can carry several audio tracks (Arabic, English, Spanish...), and ordinary downloaders either ignore them or grab only the default language.

`ytdub` solves this in four steps: you paste the URL, it reads every audio track via `yt-dlp` and shows a dubbing table, then shows a quality table (720p / 1080p / 4K), then merges your choice into one file via `ffmpeg`.

It is for anyone who wants a specific episode or film in a specific language and quality without guessing obscure `format_id` numbers. What sets it apart: picking dubs by language code (`ar`/`en`/`es`) instead of cryptic IDs, a fully bilingual Arabic/English interface (`ui_lang`), a size estimate before you commit, a non-interactive mode plus `--batch` for automation, replayable history with `--retry`, already-downloaded files skipped by default, and error messages that point you to the fix.

---

## Features

- 🔹 **Arabic + English UI** — pick your interface language on first run; saved as `ui_lang` and switchable with `--ui-lang`
- 🔹 **Dubbing table** — every available language with its type (original / dubbed / auto 🤖) and audio bitrate
- 🔹 **Quality table** — every resolution with codec, approximate size, and a "recommended ✅" mark for best compatibility
- 🔹 **Estimated size** — a combined video + dub size estimate before anything is downloaded
- 🔹 **Interactive selection** — arrow-key navigation (questionary) with smart Enter defaults
- 🔹 **Non-interactive mode** — `--url --lang --height --yes` for scripts and automation
- 🔹 **Batch mode** — `--batch urls.txt` downloads a whole list, one URL per line, with a success/failure summary
- 🔹 **Retry from history** — `--retry ID` / `--retry-last` re-runs a failed row, reusing its language and quality
- 🔹 **Skip existing** — already-downloaded files are detected by video ID and skipped (override with `--overwrite`)
- 🔹 **All dubs in one file** — `--keep-all-dubs` keeps every track in a single `mkv`
- 🔹 **Audio only** — `--audio-only` for when you just want the dub
- 🔹 **Live progress bar** — percent, size, speed, and ETA via `rich`
- 🔹 **Smart error handling** — Arabic messages with fixes (missing ffmpeg / YouTube throttling / fallback client)
- 🔹 **Resume + retry** — failed downloads resume from `.part` where they stopped, with configurable attempts and wait time
- 🔹 **Throttled update check** — checks PyPI at most once per interval (default 24h) and upgrades `yt-dlp` and friends (silently offline-safe)
- 🔹 **First-run setup** — one-time questions saved to `config.json` (retries, auto-update, save folder)
- 🔹 **Download history** — a local SQLite log of every URL: succeeded / failed / resumed / retried / skipped (`--history`)

---

## Architecture

The `youtube.py` layer is isolated and holds all `yt-dlp` logic, `downloader.py` handles downloading, and `ui.py` is display-only — no rendering logic inside the downloader.

```
config → throttled update check → URL → fetch_info (no download) → dubbing + quality tables
    → estimated size → build_format (exact -f string)
    → skip if the file already exists (unless --overwrite)
    → download with resume/retries + ffmpeg merge
    → mp4/mkv file + history row (success / failed / resumed / retried / skipped)
```

Batch and retry reuse the same per-URL step: `--batch` runs it for every line and prints a
summary, while `--retry` / `--retry-last` reload a stored row and replay it non-interactively.

### Layer Responsibilities

| Layer | Responsibility | Components |
|---|---|---|
| Commands | Main flow and options | `cli.py`, `__main__.py` |
| Extraction | Fetching data, grouping dubs, building formats | `youtube.py`, `models.py` |
| Display | Tables, prompts, progress bar | `ui.py` |
| Download | `ffmpeg` check, retry loop, resume via `yt-dlp` | `downloader.py` |
| Settings | First-run wizard, `config.json` load/save | `config.py` |
| Updates | PyPI version check + self-upgrade | `updater.py` |
| History | SQLite log of every download + statuses | `store.py` |
| i18n | Arabic/English message catalog + language switch | `i18n.py` |
| Helpers | URL validation, size formatting, language names, batch parsing, existing-file detection | `utils.py` |

---

## Project Structure

```
ytdub/
├── src/ytdub/              # Source code
│   ├── __init__.py
│   ├── __main__.py         # Entry point: python -m ytdub
│   ├── cli.py              # Commands and interactive flow
│   ├── youtube.py          # yt-dlp wrapper (isolated)
│   ├── models.py           # DubTrack / Quality / VideoInfo
│   ├── ui.py               # rich tables and prompts
│   ├── downloader.py       # Download + retry loop + ffmpeg check
│   ├── config.py           # First-run wizard + config.json
│   ├── updater.py          # PyPI check + self-upgrade
│   ├── store.py            # SQLite download history
│   ├── i18n.py             # Arabic/English message catalog
│   └── utils.py            # URL validation and language names
├── tests/                  # Offline tests
│   ├── test_lang_grouping.py
│   ├── test_format_builder.py
│   ├── test_config_store.py
│   ├── test_i18n.py
│   ├── test_utils.py
│   └── fixtures/sample_info.json
├── docs/                   # Full research (8 files, Arabic)
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- `ffmpeg` + `ffprobe` (the real binaries — not the PyPI package named `ffmpeg`)
- `deno` or `node` recommended for full YouTube support (PO Token)

### Installation

```bash
# 1) ffmpeg (required)
sudo apt install ffmpeg        # Ubuntu/Debian
brew install ffmpeg            # macOS

# 2) The tool
pip install -e .

# 3) Verify
ytdub --help
ffmpeg -version
```

### First Download

```bash
# Interactive: on first run it asks for the interface language (Arabic/English),
# a few setup defaults, then the URL and your choices.
ytdub

# Or directly:
ytdub "https://www.youtube.com/watch?v=XXXX"
python -m ytdub "https://www.youtube.com/watch?v=XXXX"
```

On first run the very first question is the interface language (Arabic or English);
the rest of the wizard is shown in that language and the choice is saved as `ui_lang`.
If you already have a `config.json` from an older version, `ytdub` asks **only** that
missing question the next time you run it and leaves your other settings untouched.

---

## Usage

### Common Examples

```bash
# Fully non-interactive (Arabic dub + 1080p)
ytdub --url "URL" --lang ar --height 1080 --yes

# Audio only, in the chosen dub
ytdub --url "URL" --audio-only

# All dubs in a single mkv file
ytdub --url "URL" --keep-all-dubs

# When dubs are missing: try a fallback client
ytdub --url "URL" --player-client android --verbose

# Download a whole list (one URL per line, # comments allowed)
ytdub --batch urls.txt --lang ar --height 1080 --yes

# Re-run the last failed download from history (reuses its language + quality)
ytdub --retry-last

# Re-run a specific history row by its id
ytdub --retry 12

# Force re-download even if the file already exists
ytdub --url "URL" --lang ar --overwrite

# Show download history (succeeded / failed / resumed / retried / skipped)
ytdub --history

# Switch the interface language (persists to config.json) and exit
ytdub --ui-lang en
ytdub --ui-lang ar

# Show config file and its location
ytdub --show-config
```

---

## Batch & Automation

`--batch FILE` reads one YouTube URL per line, ignoring blank lines and `#` comments,
then processes them one by one and prints a final summary (`succeeded • failed • total`).
The exit code is `1` if any item failed, `0` otherwise — handy for scripts.

```bash
# urls.txt — one URL per line; blank lines and # comments are ignored
cat > urls.txt <<'EOF'
# Animated shorts
https://www.youtube.com/watch?v=aaaaaaaaaaa
https://youtu.be/bbbbbbbbbbb
EOF

ytdub --batch urls.txt --lang ar --height 1080 --yes
```

Every history row can be replayed without retyping options. `--retry ID` targets one row
and `--retry-last` targets the most recent failed row; both reuse the stored language,
resolution and container, and run non-interactively:

```bash
ytdub --history          # find the id of the failed row
ytdub --retry 12         # replay it
ytdub --retry-last       # or just replay the newest failure
```

Already-downloaded files are detected by video ID inside the output folder, so re-running
the same URL is a no-op by default. Pass `--overwrite` to redownload, or set
`skip_existing` to `false` in the config to always overwrite.

---

## Configuration

On the first interactive run, `ytdub` asks for the interface language first, then a few one-time setup questions, and saves them to `~/.config/ytdub/config.json` (or `%APPDATA%\ytdub` on Windows). With `--yes` the defaults (Arabic) are written silently. Existing configs from older versions are migrated by asking only for `ui_lang`, without repeating the other questions.

| Key | Default | Description |
|---|---|---|
| `ui_lang` | `"ar"` | Interface language: `"ar"` (Arabic) or `"en"` (English) |
| `resume_on_failure` | `true` | Retry failed downloads, resuming from `.part` |
| `max_retries` | `5` | Attempts after the first try (1–20) |
| `retry_wait_seconds` | `5` | Wait between attempts (1–120s) |
| `concurrent_fragments` | `4` | Parallel fragment downloads |
| `socket_timeout` | `30` | Network timeout in seconds |
| `auto_update_check` | `true` | Check PyPI for tool updates on every run |
| `auto_update_install` | `true` | Install updates automatically (`false` = notify only) |
| `update_check_interval_hours` | `24` | Minimum hours between PyPI checks (`0` = every run) |
| `default_lang` | `null` | Preset dub (e.g. `"ar"`), `null` = ask |
| `default_height` | `null` | Preset resolution (e.g. `1080`), `null` = ask |
| `output_dir` | `"downloads"` | Default save folder |
| `player_client` | `null` | Fallback YouTube client, `null` = automatic |
| `skip_existing` | `true` | Skip a URL whose output file already exists (`--overwrite` bypasses it) |

Manage it with:

```bash
ytdub --ui-lang en       # switch to English (persists) and exit
ytdub --ui-lang ar       # switch back to Arabic (persists) and exit
ytdub --show-config      # print values + file path
ytdub --reset-config     # re-run the first-run wizard
```

Download history lives beside it in `history.db` (SQLite) — view with `ytdub --history`.

### Options Reference

| Option | What it does |
|---|---|
| `--lang ar` | Pick the dub directly (ar/en/es/...) |
| `--height 1080` | Pick the resolution directly (720/1080/2160) |
| `--yes` | Skip prompts with defaults (original + 1080p) |
| `--keep-all-dubs` | All dubs in one `mkv` |
| `--prefer-av1` | Prefer AV1/VP9 over h264 (higher quality, less compatible) |
| `--audio-only` | Audio only |
| `--output-dir` | Save folder (default `downloads`) |
| `--player-client` | Fallback client (`android`/`mweb`/`ios`/`web_safari`) |
| `--cookies-from-browser chrome` | Fix throttling issues (optional) |
| `--cookies FILE` | Netscape cookies file (optional) |
| `--history` | Show download history, then exit |
| `--history-limit N` | History rows to show (default 20) |
| `--retry ID` | Re-run the history row with this id (reuses its language/quality) |
| `--retry-last` | Re-run the most recent failed history row |
| `--batch FILE` | Download every URL in a file (one per line, `#` comments allowed) |
| `--overwrite` | Redownload even if the output file already exists |
| `--show-config` | Show settings + file path, then exit |
| `--ui-lang ar\|en` | Set and save the interface language, then exit |
| `--reset-config` | Re-run the first-run wizard, then exit |
| `--verbose` | Technical details for errors |

---

## Testing & Quality

```bash
# All tests (offline — against saved fixtures)
PYTHONPATH=src python -m pytest tests/ -q

# Quick check
PYTHONPATH=src python -m ytdub --help
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ffmpeg not found` | Binary not installed | Install it via your package manager (`apt`/`brew`/`choco`) |
| `Unsupported URL` | Non-YouTube or truncated link | Paste a full `watch`/`youtu.be` link |
| `Throttled (429)` | YouTube limited the IP | Wait a bit or use `--cookies-from-browser` |
| `PO Token required` | YouTube humanity check | Update `yt-dlp` to nightly, install `deno`, then `--player-client android` |
| `DRM protected` | Encrypted content | Cannot be downloaded — by design |
| Only one dub | Video has a single original language | Normal behavior — the step is skipped |
| `Failed after N attempts` | Unstable network, retries exhausted | Raise `max_retries`/`retry_wait_seconds` in config, or re-run later — it resumes from `.part` |
| Output skipped ("موجود مسبقًا") | `skip_existing` is on and the file exists | Use `--overwrite`, or set `skip_existing` to `false` |
| `--batch` exits with code 1 | At least one URL failed | Read the per-URL errors above the summary, then fix and `--retry ID` |

---

## Disclaimer

⚠️ Disclaimer: the developer is not responsible for any misuse of this tool.

---

## License

This project is released into the public domain under the [Unlicense](LICENSE).

---

## Contributing

Contributions are welcome — please start with [CONTRIBUTING.md](CONTRIBUTING.md):

1. Run `pytest tests/ -q` and make sure all tests pass
2. Keep all `yt-dlp` logic inside `youtube.py`
3. Keep rendering logic out of `downloader.py`
4. Full design details live in `docs/`
