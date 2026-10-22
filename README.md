![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![yt-dlp](https://img.shields.io/badge/yt--dlp-core-red)
![FFmpeg](https://img.shields.io/badge/FFmpeg-required-green?logo=ffmpeg)
![License](https://img.shields.io/badge/License-Unlicense-yellow)

# ytdub

> **A bilingual terminal app that downloads a YouTube video with the dub language and quality you choose.**

[What It Does](#what-it-does) · [Features](#features) · [Themes & Responsive UI](#themes-and-responsive-ui) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Clone and Install](#clone-and-install) · [Usage](#usage) · [Smart Picks](#smart-picks) · [Configuration](#configuration) · [Testing](#testing-and-quality) · [Troubleshooting](#troubleshooting) · [Contributing](#contributing)

---

## What It Does

YouTube often ships one video with several audio tracks: the original language plus
Arabic, English, Spanish, and other dubs. Ordinary downloaders either ignore those tracks
or keep only the default one.

`ytdub` makes the choice explicit. You paste a URL, it reads every audio and video stream
through `yt-dlp`, and it shows two clean tables: available dubs and available qualities.
You pick a language and a resolution; `yt-dlp` downloads the matching streams and `ffmpeg`
merges them into one playable file.

It is built for people who want a specific episode or film in a specific language without
decoding cryptic `format_id` values. You can select dubs by language code, see an estimated
file size before downloading, run fully non-interactively, process a batch file, replay a
failed download from history, and skip files that already exist. The interface is available
in Arabic and English, with three visual themes that adapt to the terminal width.

---

## Features

- **Arabic and English UI** — choose the interface language on first run; saved as `ui_lang` and switchable with `--ui-lang`.
- **Three interface themes** — Classic (adaptive terminal colors), Midnight (soft blue for dark terminals), and Sand (warm tones for light terminals). Saved as `ui_theme`, switchable with `--theme`, or previewed interactively with `--theme-menu`.
- **Smart picks** — learns your dub and quality choices locally; when enabled, it selects them automatically. A missing favorite dub stops the run, while a missing quality is upgraded to the nearest higher option.
- **Responsive layout** — tables and panels follow the terminal width (`compact` / `regular` / `wide`), drop secondary columns when space is tight, and cap at a comfortable reading width.
- **Eye-friendly design** — semantic theme styles, soft accents, and contrast tuned for each background; no raw ANSI colors scattered through the flow.
- **Developer notation, no emoji** — statuses use plain log-style tags (`OK ·`, `ERR ·`, `WARN ·`, `RETRY ·`, `SKIP ·`, `INFO ·`) with geometric markers (`◆`, `›`, `·`, `→`), so output stays consistent in every terminal and pipe.
- **Dubbing table** — every audio language with its type (original / dubbed / auto-dub), code, and bitrate.
- **Quality table** — every resolution with codec, approximate size, and a compatibility note.
- **Size estimate** — combined video + selected dub size before anything is downloaded.
- **Interactive selection** — arrow-key navigation through `questionary` with smart defaults.
- **Non-interactive mode** — `--url --lang --height --yes` for scripts and automation.
- **Batch mode** — `--batch urls.txt` downloads a list with a final success/failure summary.
- **Retry from history** — `--retry ID` and `--retry-last` replay a failed row with its stored settings.
- **Skip existing** — files are matched by video ID and skipped by default; `--overwrite` forces a download.
- **All dubs in one file** — `--keep-all-dubs` keeps every audio track in a single `mkv`.
- **Audio only** — `--audio-only` downloads just the selected dub.
- **Live progress** — percentage, downloaded size, speed, and ETA through `rich`.
- **Resume and retry** — interrupted downloads resume from `.part` with configurable attempts and wait time.
- **Throttled update check** — checks PyPI at most once per interval and upgrades the tool stack, silently failing offline.
- **Download history** — a local SQLite log of every URL with statuses: succeeded, failed, resumed, retried, or skipped.

---

## Themes and Responsive UI

The interface ships with three deliberately different designs. Pick the one that matches
your terminal background and lighting conditions:

| Theme | Best for | Character |
|---|---|---|
| `classic` | Any terminal (default) | Adaptive ANSI colors, balanced contrast, closest to a stock CLI |
| `midnight` | Dark backgrounds | Soft blue and lavender night palette with muted borders |
| `sand` | Light backgrounds | Warm, low-blue tones designed for daytime comfort |

```bash
# Apply and persist a theme
ytdub --theme midnight

# Apply a theme and continue with a download in the same run
ytdub --theme sand --url "URL" --lang ar --height 1080

# Browse all themes with a live preview
ytdub --theme-menu
```

The theme is saved in `config.json` as `ui_theme` and restored on every run. The first-run
wizard asks for it right after the interface language.

**Responsive behaviour** is computed from the real terminal width:

| Width | Layout | What changes |
|---|---|---|
| `< 62` columns | `compact` | Secondary columns are hidden; only the essential dub and quality fields remain |
| `62–95` columns | `regular` | Core columns stay; FPS, codec, and other optional fields are reduced |
| `>= 96` columns | `wide` | Full tables, including FPS, codec, and compatibility notes |

Panels and tables stop at `110` columns so long lines stay readable on ultrawide terminals.
On very narrow screens, the video title moves inside the panel so it wraps instead of being
cropped. The same rendering functions power real runs and the `--theme-menu` preview, so
what you see is what you get.

### Output Notation

The interface uses a small, emoji-free notation so output renders identically in every
terminal, font, and pipe:

| Marker | Meaning |
|---|---|
| `OK ·` | Operation completed successfully |
| `ERR ·` | Operation failed |
| `WARN ·` | Warning or retry reason |
| `RETRY ·` | Retry in progress |
| `SKIP ·` | Existing file or item skipped |
| `INFO ·` | Availability or status information |
| `◆` | Section, table, or panel title |
| `›` | Input prompt |
| `·` | Separator between values |
| `→` | Transition between states |

These markers live in `i18n.py`, and the test suite rejects emoji ranges to prevent them
from creeping back in.

---

## Architecture

`yt-dlp` knowledge is isolated in one module, downloading in another, and rendering in a
third. The CLI only orchestrates. This keeps extraction quirks, network side effects, and
terminal layout independently testable.

```
config + theme + update check
    → URL → fetch_info (metadata only)
    → group dubs + qualities → render tables
    → user picks language + quality
    → estimate size
    → build the exact -f format string
    → skip if the output already exists (unless --overwrite)
    → download with resume/retries + ffmpeg merge
    → mp4/mkv/m4a file + history row
```

Batch and retry reuse the same per-URL pipeline: `--batch` runs it for every line and prints
a summary, while `--retry` / `--retry-last` reload a stored row and replay it
non-interactively.

### Layer Responsibilities

| Layer | Responsibility | Components |
|---|---|---|
| Commands | Option parsing, setup, and the per-URL flow | `cli.py`, `__main__.py` |
| Extraction | Fetching data, grouping dubs/qualities, building formats, estimating size | `youtube.py`, `models.py` |
| Display | Panels, tables, prompts, progress bar, responsive layout | `ui.py` |
| Themes | Palettes, aliases, labels, and theme metadata | `themes.py` |
| Download | `ffmpeg` check, retry loop, resume via `yt-dlp` | `downloader.py` |
| Settings | First-run wizard, `config.json` load/save | `config.py` |
| Updates | PyPI version check and self-upgrade | `updater.py` |
| History | SQLite log of every download and its status | `store.py` |
| i18n | Arabic/English message catalog and language switch | `i18n.py` |
| Preferences | Local learned dub/quality counts | `preferences.py` |
| Auto-pick | Learned dub matching and quality upgrades | `autopick.py` |
| Helpers | URL validation, formatting, language names, batch parsing, existing-file detection | `utils.py` |

### Design Rules

- All `yt-dlp` logic lives in `youtube.py`; no format strings leak into other modules.
- `downloader.py` reports progress through a callback and never renders.
- Rendering stays in `ui.py`; colors come only from `themes.py`, and strings come only from `i18n.py`.
- `config.py`, `store.py`, and `updater.py` are infrastructure with no UI except the setup wizard.
- Tests run offline against `tests/fixtures/sample_info.json`; live YouTube responses are flaky and throttled.
- Paths and titles are escaped before printing because they can contain `[<video_id>]`, which `rich` would otherwise parse as markup.

---

## Project Structure

```
ytdub/
├── src/ytdub/                  # Source code
│   ├── __init__.py             # Version marker
│   ├── __main__.py             # python -m ytdub entry point
│   ├── cli.py                  # Click options and orchestration
│   ├── youtube.py              # yt-dlp extraction and format building
│   ├── models.py               # DubTrack / Quality / VideoInfo
│   ├── ui.py                   # Rich tables, prompts, progress, responsive layout
│   ├── themes.py               # Three semantic palettes
│   ├── downloader.py           # Download, retry loop, ffmpeg check
│   ├── config.py               # First-run wizard and config.json
│   ├── updater.py              # PyPI check and self-upgrade
│   ├── store.py                # SQLite download history
│   ├── i18n.py                 # Arabic/English message catalog
│   ├── preferences.py          # Local learned dub/quality counts
│   ├── autopick.py             # Matching and quality-upgrade rules
│   └── utils.py                # URL rules, formatting, batch helpers
├── tests/                      # Offline test suite
│   ├── test_lang_grouping.py
│   ├── test_format_builder.py
│   ├── test_config_store.py
│   ├── test_i18n.py
│   ├── test_smart.py           # preferences, auto-pick rules, CLI flag
│   ├── test_themes.py
│   ├── test_utils.py
│   └── fixtures/sample_info.json
├── docs/                       # Design research (8 files, Arabic)
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## Quick Start

### Prerequisites

- Python 3.10 or newer.
- `ffmpeg` and `ffprobe` as real system binaries. The PyPI package named `ffmpeg` does **not** count.
- `deno` or `node` recommended for full YouTube support (PO Token and SABR cases).

```bash
# Install ffmpeg with your platform package manager
sudo apt install ffmpeg        # Ubuntu / Debian
sudo dnf install ffmpeg        # Fedora
brew install ffmpeg            # macOS
choco install ffmpeg           # Windows (Chocolatey)
```

Confirm the binaries are visible before installing the Python package:

```bash
ffmpeg -version
ffprobe -version
```

### Clone and Install

```bash
# 1) Clone the repository
git clone https://github.com/amjdcodes/ytdub.git
cd ytdub

# 2) Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell:
# .venv\Scripts\Activate.ps1
# Windows CMD:
# .venv\Scripts\activate.bat

# 3) Upgrade pip and install the project with its runtime dependencies
python -m pip install --upgrade pip
pip install -e .

# 4) Optional: install the test runner for development
pip install pytest

# 5) Verify the command and the ffmpeg binary
ytdub --help
ytdub --version
ffmpeg -version
```

`pip install -e .` reads `pyproject.toml` and installs the runtime stack
(`yt-dlp[default]`, `rich`, `click`, and `questionary`). It also registers the
`ytdub` command inside the active virtual environment.

The matching `ffmpeg` binary is a system dependency and is not installed by
`pip`. Install it first using the command for your platform in
[Prerequisites](#prerequisites).

To run the test suite from the cloned repository:

```bash
PYTHONPATH=src python -m pytest tests/ -q
```

### First Download

```bash
# Fully interactive: language, theme, setup defaults, URL, dub, quality
ytdub

# Or pass the URL directly
ytdub "https://www.youtube.com/watch?v=XXXX"

# Run without installing
PYTHONPATH=src python -m ytdub "https://www.youtube.com/watch?v=XXXX"
```

On first run the wizard asks for the interface language, the theme, retry/update
preferences, and whether to enable smart picks. Everything is saved in
`~/.config/ytdub/config.json` on Linux and macOS, or `%APPDATA%/ytdub/config.json` on
Windows. Learned picks are stored beside it in `preferences.json`. Later runs reuse the
saved settings.

If an older `config.json` is missing `ui_lang`, `ytdub` asks only that question and keeps the
rest of the file untouched. A missing `ui_theme` silently falls back to `classic`.

---

## Usage

### Common Examples

```bash
# Fully non-interactive: Arabic dub, 1080p
ytdub --url "URL" --lang ar --height 1080 --yes

# Audio only, in the chosen dub
ytdub --url "URL" --audio-only

# All dubs in a single mkv file
ytdub --url "URL" --keep-all-dubs

# Prefer AV1/VP9 over H.264
ytdub --url "URL" --lang ar --height 2160 --prefer-av1

# When dubs are missing, try a fallback player client
ytdub --url "URL" --player-client android --verbose

# Download a list: one URL per line, blank lines and # comments ignored
ytdub --batch urls.txt --lang ar --height 1080 --yes

# Replay the newest failed history row
ytdub --retry-last

# Replay a specific history row
ytdub --retry 12

# Force a re-download even if the file already exists
ytdub --url "URL" --lang ar --overwrite

# Inspect history and settings
ytdub --history
ytdub --show-config

# Switch language or theme (persists to config.json) and exit
ytdub --ui-lang en
ytdub --ui-lang ar
ytdub --theme midnight
ytdub --theme-menu
```

### Output Naming and Containers

Files are written to `downloads/` by default and include the video ID:

```
downloads/<Video Title> [<video_id>].<container>
```

| Selection | Container | Notes |
|---|---|---|
| One dub + quality | `mp4` | H.264 preferred for compatibility unless `--prefer-av1` |
| Audio only | `m4a` | Selected dub, no video stream |
| `--keep-all-dubs` | `mkv` | All audio tracks in one file via `audio_multistreams` |

Already-downloaded files are detected by the `[<video_id>]` token, so re-running the same URL
is a no-op by default. Use `--overwrite`, or set `skip_existing` to `false`, to download again.

---

## Batch & Automation

`--batch FILE` reads one YouTube URL per line, ignores blank lines and `#` comments, then
processes the list and prints a final summary (`succeeded`, `failed`, `total`). The exit code
is `1` if any item failed and `0` otherwise, which makes it safe to use in scripts.

```bash
cat > urls.txt <<'EOF'
# Documentaries
https://www.youtube.com/watch?v=aaaaaaaaaaa
https://youtu.be/bbbbbbbbbbb
EOF

ytdub --batch urls.txt --lang ar --height 1080 --yes
```

Every history row can be replayed without retyping options. `--retry ID` targets one row;
`--retry-last` targets the most recent failed row. Both reuse the stored language, resolution,
and container, and run non-interactively.

```bash
ytdub --history          # find the failed row id
ytdub --retry 12         # replay that row
ytdub --retry-last       # or replay the newest failure
```

---

## Smart Picks

Smart picks turn your own choices into defaults. Every interactive pick, or an
explicit `--lang` / `--height`, is counted locally in `preferences.json` next to
`config.json`. When the feature is enabled, the most frequent choice becomes the
automatic pick for future runs; ties go to your most recent choice. On the first
enable, existing successful history is used to seed the counts, so the tool does
not start from zero. Nothing leaves your machine.

```bash
# Enable and persist smart picks
ytdub --smart

# Disable and go back to prompting
ytdub --no-smart

# Enable for this run and continue downloading
ytdub --smart --url "URL"
```

The selection rules are intentionally strict and predictable:

| Situation | Behaviour |
|---|---|
| Learned dub is available | Selected automatically |
| Learned dub is missing | The run stops with an error listing available dubs; no silent fallback |
| Learned quality is available | Selected automatically |
| Learned quality is missing | The nearest higher quality is chosen |
| No quality is higher than the learned one | The highest available quality is chosen, with a warning |
| `--lang` or `--height` is passed | The explicit flag wins and is recorded as the new preference |
| `--keep-all-dubs` is used | Smart picking is bypassed because no single dub/quality is selected |
| `--audio-only` is used | The learned dub is used; the quality step is skipped |

Only choices that come from you are recorded. Automatic smart picks are not fed
back into the counters, so the preference does not drift on its own.

---

## Configuration

Settings live in `~/.config/ytdub/config.json` (Linux/macOS) or
`%APPDATA%/ytdub/config.json` (Windows). The first-run wizard writes them interactively;
`--yes` writes Arabic + classic defaults silently.

| Key | Default | Description |
|---|---|---|
| `ui_lang` | `"ar"` | Interface language: `"ar"` or `"en"` |
| `ui_theme` | `"classic"` | Visual theme: `"classic"`, `"midnight"`, or `"sand"` |
| `smart_picks` | `false` | Learn your dub/quality choices and select them automatically |
| `resume_on_failure` | `true` | Retry failed downloads, resuming from `.part` |
| `max_retries` | `5` | Retries after the first attempt (1–20) |
| `retry_wait_seconds` | `5` | Wait between attempts (1–120 seconds) |
| `concurrent_fragments` | `4` | Parallel fragment downloads |
| `socket_timeout` | `30` | Network timeout in seconds |
| `auto_update_check` | `true` | Check PyPI for tool updates on startup |
| `auto_update_install` | `true` | Install updates automatically; `false` only notifies |
| `update_check_interval_hours` | `24` | Minimum hours between PyPI checks; `0` checks every run |
| `default_lang` | `null` | Preset dub code (for example `"ar"`); `null` asks |
| `default_height` | `null` | Preset resolution (for example `1080`); `null` asks |
| `output_dir` | `"downloads"` | Default save folder |
| `player_client` | `null` | Fallback YouTube client; `null` selects automatically |
| `skip_existing` | `true` | Skip a URL whose output file exists; `--overwrite` bypasses it |

Manage configuration with:

```bash
ytdub --ui-lang en       # switch to English and exit
ytdub --ui-lang ar       # switch to Arabic and exit
ytdub --theme midnight   # apply and save a theme
ytdub --smart            # enable learned automatic picks
ytdub --no-smart         # disable automatic picks
ytdub --show-config      # print values and the config path
ytdub --reset-config     # re-run the first-run wizard
```

Download history lives beside the config in `history.db` (SQLite). View it with `ytdub --history`. Learned smart-pick counts live in `preferences.json`.

### Options Reference

| Option | Description |
|---|---|
| `--lang ar` | Pick the dub directly (`ar`/`en`/`es`/...) |
| `--height 1080` | Pick the resolution directly (720/1080/2160) |
| `--yes` | Skip prompts with defaults (original dub + 1080p) |
| `--keep-all-dubs` | Keep all dubs in one `mkv` |
| `--prefer-av1` | Prefer AV1/VP9 over H.264 |
| `--audio-only` | Download audio only |
| `--output-dir` | Save folder (default from config) |
| `--player-client` | Fallback client: `android`, `mweb`, `ios`, `web_safari` |
| `--cookies-from-browser chrome` | Read cookies from a browser to fix throttling |
| `--cookies FILE` | Netscape cookies file |
| `--history` | Show download history, then exit |
| `--history-limit N` | Number of history rows to show (default 20) |
| `--retry ID` | Replay a specific history row |
| `--retry-last` | Replay the most recent failed row |
| `--batch FILE` | Download every URL in a file |
| `--overwrite` | Re-download even if the output exists |
| `--show-config` | Show settings and the config path, then exit |
| `--ui-lang ar\|en` | Set and save the interface language, then exit |
| `--theme classic\|midnight\|sand` | Set and save the interface theme |
| `--theme-menu` | Interactive theme picker with a live preview |
| `--smart` / `--no-smart` | Enable or disable automatic picks from learned preferences |
| `--reset-config` | Re-run the first-run wizard, then exit |
| `--verbose` | Print technical error details |

---

## Testing and Quality

The test suite is offline and fixture-based; it never contacts YouTube.

```bash
# Run everything
PYTHONPATH=src python -m pytest tests/ -q

# Smoke check without installing
PYTHONPATH=src python -m ytdub --help
```

The suite covers dub grouping, format strings, size estimates, retry/resume behavior,
config migration, history storage, i18n key parity, theme palettes, responsive breakpoints,
the theme preview, learned preferences, and the smart-pick quality policy.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ffmpeg not found` | Binary not installed | Install it with `apt`, `brew`, `dnf`, or `choco` |
| `Unsupported URL` | Non-YouTube or truncated link | Paste a full `watch` or `youtu.be` link |
| `Throttled (429)` | YouTube limited the IP | Wait, or use `--cookies-from-browser` |
| `PO Token required` | YouTube humanity check | Update `yt-dlp` to nightly, install `deno`, then use `--player-client android` |
| `DRM protected` | Encrypted content | Cannot be downloaded by design |
| Only one dub is listed | The video has a single original language | Normal; the dub step is skipped |
| `Failed after N attempts` | Unstable network or exhausted retries | Raise `max_retries`/`retry_wait_seconds`, or re-run later; it resumes from `.part` |
| Output skipped | `skip_existing` is on and the file exists | Use `--overwrite`, or set `skip_existing` to `false` |
| `--batch` exits with code 1 | At least one URL failed | Read the per-URL errors, fix them, then use `--retry ID` |
| A theme is hard to read | The palette does not match the terminal background | Use `midnight` on dark backgrounds, `sand` on light ones, or `classic` for automatic terminal colors |
| Smart picks stop with "preferred dub is unavailable" | The learned dub is not in this video | Use `--no-smart` for this run, pass `--lang CODE`, or pick a new dub manually to retrain |

---

## Disclaimer

**Disclaimer:** the developer is not responsible for any misuse of this tool. Respect
copyright, platform terms, and local law when downloading content.

---

## License

This project is released into the public domain under the [Unlicense](LICENSE).

---

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md):

1. Run `PYTHONPATH=src python -m pytest tests/ -q` and make sure every test passes.
2. Keep all `yt-dlp` logic inside `youtube.py`.
3. Keep rendering out of `downloader.py`; colors belong in `themes.py`, strings in `i18n.py`.
4. Add a test for any behavior change: grouping/format tests, config/store tests, theme tests, or i18n tests as appropriate.
5. Never commit cookies, credentials, `.env` files, downloaded media, or `downloads/`.
6. Full design rationale lives in `docs/` (8 Arabic research files).
