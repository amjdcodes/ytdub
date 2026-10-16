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

It is for anyone who wants a specific episode or film in a specific language and quality without guessing obscure `format_id` numbers. What sets it apart: picking dubs by language code (`ar`/`en`/`es`) instead of cryptic IDs, a non-interactive mode for automation, and Arabic error messages that point you to the fix.

---

## Features

- 🔹 **Dubbing table** — every available language with its type (original / dubbed / auto 🤖) and audio bitrate
- 🔹 **Quality table** — every resolution with codec, approximate size, and a "recommended ✅" mark for best compatibility
- 🔹 **Interactive selection** — arrow-key navigation (questionary) with smart Enter defaults
- 🔹 **Non-interactive mode** — `--url --lang --height --yes` for scripts and automation
- 🔹 **All dubs in one file** — `--keep-all-dubs` keeps every track in a single `mkv`
- 🔹 **Audio only** — `--audio-only` for when you just want the dub
- 🔹 **Live progress bar** — percent, size, speed, and ETA via `rich`
- 🔹 **Smart error handling** — Arabic messages with fixes (missing ffmpeg / YouTube throttling / fallback client)
- 🔹 **Resume + retry** — failed downloads resume from `.part` where they stopped, with configurable attempts and wait time
- 🔹 **Self-updating** — checks PyPI on every run and upgrades `yt-dlp` and friends (silently offline-safe)
- 🔹 **First-run setup** — one-time questions saved to `config.json` (retries, auto-update, save folder)
- 🔹 **Download history** — a local SQLite log of every URL: succeeded / failed / resumed / retried (`--history`)

---

## Architecture

The `youtube.py` layer is isolated and holds all `yt-dlp` logic, `downloader.py` handles downloading, and `ui.py` is display-only — no rendering logic inside the downloader.

```
config → update check → URL → fetch_info (no download) → dubbing + quality tables
    → build_format (exact -f string) → download with resume/retries + ffmpeg merge
    → mp4/mkv file + history row (success / failed / resumed / retried)
```

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
| Helpers | URL validation, size formatting, language names | `utils.py` |

---

## Project Structure

```
YouTube_Download_Dubbing/
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
│   └── utils.py            # URL validation and language names
├── tests/                  # Offline tests
│   ├── test_lang_grouping.py
│   ├── test_format_builder.py
│   ├── test_config_store.py
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
# Interactive: asks for the URL, then shows the tables
ytdub

# Or directly:
ytdub "https://www.youtube.com/watch?v=XXXX"
python -m ytdub "https://www.youtube.com/watch?v=XXXX"
```

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

# Show download history (succeeded / failed / resumed / retried)
ytdub --history

# Show config file and its location
ytdub --show-config
```

---

## Configuration

On the first interactive run, `ytdub` asks a few one-time questions and saves them to `~/.config/ytdub/config.json` (or `%APPDATA%\ytdub` on Windows). With `--yes` the defaults are written silently.

| Key | Default | Description |
|---|---|---|
| `resume_on_failure` | `true` | Retry failed downloads, resuming from `.part` |
| `max_retries` | `5` | Attempts after the first try (1–20) |
| `retry_wait_seconds` | `5` | Wait between attempts (1–120s) |
| `concurrent_fragments` | `4` | Parallel fragment downloads |
| `socket_timeout` | `30` | Network timeout in seconds |
| `auto_update_check` | `true` | Check PyPI for tool updates on every run |
| `auto_update_install` | `true` | Install updates automatically (`false` = notify only) |
| `default_lang` | `null` | Preset dub (e.g. `"ar"`), `null` = ask |
| `default_height` | `null` | Preset resolution (e.g. `1080`), `null` = ask |
| `output_dir` | `"downloads"` | Default save folder |
| `player_client` | `null` | Fallback YouTube client, `null` = automatic |

Manage it with:

```bash
ytdub --show-config     # print values + file path
ytdub --reset-config    # re-run the first-run wizard
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
| `--show-config` | Show settings + file path, then exit |
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
