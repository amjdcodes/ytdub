import pytest

import ytdub.config as config
import ytdub.ui as ui
from ytdub import themes
from ytdub.models import DubTrack, Quality


@pytest.fixture(autouse=True)
def _restore_theme_and_language():
    from ytdub.i18n import get_lang, set_lang

    old_theme, old_lang = ui.get_theme(), get_lang()
    yield
    ui.set_theme(old_theme)
    set_lang(old_lang)


def test_three_themes_and_aliases():
    assert themes.THEME_NAMES == ("classic", "midnight", "sand")
    assert themes.DEFAULT_THEME == "classic"
    assert themes.normalize_theme(None) == "classic"
    assert themes.normalize_theme("") == "classic"
    assert themes.normalize_theme("DEFAULT") == "classic"
    assert themes.normalize_theme("Night") == "midnight"
    assert themes.normalize_theme("dark") == "midnight"
    assert themes.normalize_theme("Warm") == "sand"
    assert themes.normalize_theme("light") == "sand"
    assert themes.normalize_theme("does-not-exist") == "classic"


def test_every_palette_defines_the_same_complete_keys():
    reference = set(themes.PALETTES["classic"])
    for name in themes.THEME_NAMES:
        assert set(themes.PALETTES[name]) == reference, name
        assert all(isinstance(v, str) and v.strip() for v in themes.PALETTES[name].values()), name


def test_theme_labels_and_descriptions_are_translated():
    ui.set_theme("midnight")
    assert themes.theme_label("midnight") == "ليلي"
    assert themes.theme_description("sand")
    from ytdub.i18n import set_lang

    set_lang("en")
    try:
        assert themes.theme_label("midnight") == "Midnight"
        assert "dark" in themes.theme_description("midnight").lower()
    finally:
        set_lang("ar")


def test_set_theme_applies_rich_styles():
    assert ui.set_theme("midnight") == "midnight"
    assert ui.get_theme() == "midnight"
    assert ui.console.get_style("primary").color is not None
    assert ui.set_theme("sand") == "sand"
    assert ui.get_theme() == "sand"
    assert ui.set_theme("classic") == "classic"
    assert ui.get_theme() == "classic"


def test_layout_breakpoints_are_responsive():
    assert ui.layout(40) == "compact"
    assert ui.layout(61) == "compact"
    assert ui.layout(62) == "regular"
    assert ui.layout(95) == "regular"
    assert ui.layout(96) == "wide"
    assert ui.layout(200) == "wide"


def test_content_width_is_clamped_for_readability():
    width = ui.content_width()
    assert 24 <= width <= ui.MAX_CONTENT_WIDTH


def test_compact_tables_drop_secondary_columns(monkeypatch):
    from ytdub.i18n import set_lang

    set_lang("en")
    try:
        monkeypatch.setattr(ui, "content_width", lambda: 50)
        dubs = [DubTrack(1, "ar", "العربية", "dubbed", abr=128.0), DubTrack(2, "en", "English", "original")]
        with ui.console.capture() as cap:
            ui.show_dubs_table(dubs)
        text = cap.get()
        assert "العربية" in text
        assert "Code" not in text

        monkeypatch.setattr(ui, "content_width", lambda: 110)
        with ui.console.capture() as cap_wide:
            ui.show_dubs_table(dubs)
        assert "Code" in cap_wide.get()
    finally:
        set_lang("ar")


def test_qualities_hide_note_column_when_empty(monkeypatch):
    from ytdub.i18n import set_lang

    set_lang("en")
    try:
        monkeypatch.setattr(ui, "content_width", lambda: 110)
        quals = [Quality(1, 1080, 60, "avc1", 1_000_000_000)]
        with ui.console.capture() as cap:
            ui.show_qualities_table(quals)
        assert "Note" not in cap.get()
    finally:
        set_lang("ar")


def test_compact_qualities_hide_optional_columns(monkeypatch):
    from ytdub.i18n import set_lang

    set_lang("en")
    try:
        monkeypatch.setattr(ui, "content_width", lambda: 50)
        quals = [Quality(1, 1080, 60, "avc1", 1_000_000_000, note="Recommended")]
        with ui.console.capture() as cap:
            ui.show_qualities_table(quals)
        text = cap.get()
        assert "Note" not in text and "Codec" not in text
    finally:
        set_lang("ar")


def test_theme_preview_renders_without_errors():
    with ui.console.capture() as cap:
        ui.set_theme("sand")
        ui.show_theme_preview()
    text = cap.get()
    assert "Español" in text and "1080p" in text


def test_config_defaults_include_classic_theme():
    assert config.DEFAULTS["ui_theme"] == "classic"


def test_cli_theme_flag_persists_choice(tmp_path, monkeypatch):
    import json

    from click.testing import CliRunner

    import ytdub.cli as cli
    from ytdub.i18n import get_lang, set_lang

    old_lang = get_lang()
    monkeypatch.setattr(config, "app_dir", lambda: str(tmp_path))
    try:
        result = CliRunner().invoke(cli.main, ["--theme", "sand"])
        assert result.exit_code == 0
        saved = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
        assert saved["ui_theme"] == "sand"
        assert ui.get_theme() == "sand"
    finally:
        set_lang(old_lang)
