![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![yt-dlp](https://img.shields.io/badge/yt--dlp-core-red)
![FFmpeg](https://img.shields.io/badge/FFmpeg-required-green?logo=ffmpeg)
![License](https://img.shields.io/badge/License-Unlicense-yellow)

# ytdub

> **A Python CLI that downloads a YouTube video with the dubbing language and quality you pick from two tidy tables.**

[What It Does](#what-it-does) · [Quick Start](#quick-start) · [Usage](#usage) · [Architecture](#architecture) · [Troubleshooting](#troubleshooting) · [Contributing](#contributing)

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

---

## Architecture

The `youtube.py` layer is isolated and holds all `yt-dlp` logic, `downloader.py` handles downloading, and `ui.py` is display-only — no rendering logic inside the downloader.

```
URL → fetch_info (no download) → dubbing + quality tables
    → build_format (exact -f string) → download + ffmpeg merge → mp4/mkv file
```

### Layer Responsibilities

| Layer | Responsibility | Components |
|---|---|---|
| Commands | Main flow and options | `cli.py`, `__main__.py` |
| Extraction | Fetching data, grouping dubs, building formats | `youtube.py`, `models.py` |
| Display | Tables, prompts, progress bar | `ui.py` |
| Download | `ffmpeg` check and downloading via `yt-dlp` | `downloader.py` |
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
│   ├── downloader.py       # Download + ffmpeg check
│   └── utils.py            # URL validation and language names
├── tests/                  # Offline tests
│   └── fixtures/sample_info.json
├── docs/                   # Full research (8 files, Arabic)
├── pyproject.toml
└── README.md
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
```

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
