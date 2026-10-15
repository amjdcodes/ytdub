# Contributing to ytdub

Thanks for your interest in contributing. This guide keeps the codebase consistent — please read it before opening a pull request.

## How to Contribute

1. Fork the repository and create a branch for your change.
2. Make your change following the architecture rules below.
3. Run the test suite and make sure everything passes.
4. Open a pull request with a clear description of what changed and why.

## Architecture Rules (Mandatory)

The project is layered on purpose — respect these boundaries:

- **All `yt-dlp` logic lives in `src/ytdub/youtube.py` only.** Fetching info, grouping dubs/qualities, and building format strings must not leak into other modules.
- **No rendering logic in `src/ytdub/downloader.py`.** The downloader receives a `progress_cb` and reports through it; `ui.py` does the drawing.
- **Display code belongs in `src/ytdub/ui.py`.** Tables, prompts, and progress bars stay there.
- **CLI flow belongs in `src/ytdub/cli.py`.** Argument parsing and the URL → dub → quality → download flow stay there.

## Testing

Tests run offline against saved fixtures — no network access required:

```bash
pip install -e . pytest
PYTHONPATH=src python -m pytest tests/ -q
```

- Add or update tests in `tests/` for any change to grouping or format-building logic.
- Store new test data as JSON under `tests/fixtures/` (anonymized, minimal).
- All tests must pass before a PR is accepted.

## Code Style

- Python 3.10+ (see `requires-python` in `pyproject.toml`).
- Keep functions small and typed where practical.
- User-facing messages stay concise; technical details go behind `--verbose`.
- Do not add new third-party dependencies without justification in the PR — the stack (`yt-dlp`, `rich`, `click`, `questionary`) is chosen deliberately (see `docs/`).

## What Not to Do

- Do not attempt to bypass DRM or age restrictions.
- Do not commit cookies, credentials, or downloaded media files.
- Do not commit `.env` files or any real user data.

## Design Reference

The full technical research behind every design decision lives in `docs/` (8 files). Check the relevant file before changing behavior around dubbing, formats, merging, or error handling.
