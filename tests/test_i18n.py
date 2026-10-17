import json
import re

import pytest

import ytdub.config as config
import ytdub.i18n as i18n


class FakeConsole:
    """بديل بسيط لـ rich.Console: يسجّل الأسئلة ويعيد إجابات مرتّبة."""

    def __init__(self, answers):
        self.answers = iter(answers)
        self.prompts = []
        self.lines = []

    def print(self, *args, **kwargs):
        self.lines.append(" ".join(str(a) for a in args))

    def input(self, prompt=""):
        self.prompts.append(prompt)
        return next(self.answers)


@pytest.fixture(autouse=True)
def _restore_language():
    old = i18n.get_lang()
    yield
    i18n.set_lang(old)


def test_catalogs_have_identical_keys_and_no_empty_values():
    ar, en = i18n._MESSAGES["ar"], i18n._MESSAGES["en"]
    assert set(ar) == set(en)
    for lang, table in (("ar", ar), ("en", en)):
        assert all(isinstance(v, str) and v.strip() for v in table.values()), lang


def test_default_language_is_arabic():
    i18n.set_lang(None)
    assert i18n.get_lang() == "ar"
    assert i18n.t("status.success") == "نجح"


def test_catalogs_contain_no_emoji_or_pictographs():
    # العائلة المعتمدة: وسوم نصية [ok]/[err]/[warn]/[retry]/[skip] ورموز
    # هندسية ◆ › · → فقط. أي إيموجي أو رمز تصويري يفشل هذا الاختبار.
    forbidden = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")
    for lang, table in i18n._MESSAGES.items():
        for key, value in table.items():
            match = forbidden.search(value)
            assert match is None, f"{lang}:{key} contains {match.group(0)!r}"


def test_switch_to_english_and_back():
    i18n.set_lang("en")
    assert i18n.get_lang() == "en"
    assert i18n.t("status.success") == "Succeeded"
    assert "Batch" in i18n.t("batch.started", count=3, file="x.txt")
    i18n.set_lang("ar")
    assert i18n.t("status.success") == "نجح"


def test_english_aliases_normalize():
    assert i18n.set_lang("English") == "en"
    assert i18n.set_lang("EN") == "en"
    assert i18n.set_lang("fr") == "ar"


def test_missing_key_falls_back_to_arabic_then_key():
    i18n.set_lang("en")
    assert i18n.t("does.not.exist") == "does.not.exist"


def test_config_defaults_include_ui_lang():
    assert config.DEFAULTS["ui_lang"] == "ar"


def test_existing_config_missing_ui_lang_asks_only_language(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "ytdub"
    cfg_dir.mkdir()
    path = cfg_dir / "config.json"
    path.write_text(json.dumps({"max_retries": 2, "output_dir": "media"}), encoding="utf-8")
    monkeypatch.setattr(config, "app_dir", lambda: str(cfg_dir))

    con = FakeConsole(["2"])
    cfg, _ = config.ensure(con, non_interactive=False)

    assert cfg["ui_lang"] == "en"
    assert cfg["max_retries"] == 2 and cfg["output_dir"] == "media"
    assert i18n.get_lang() == "en"
    assert len(con.prompts) == 1  # سؤال اللغة فقط، لا إعادة للمعالج
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["ui_lang"] == "en" and saved["max_retries"] == 2


def test_existing_config_missing_ui_lang_non_interactive_uses_default(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "ytdub"
    cfg_dir.mkdir()
    (cfg_dir / "config.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(config, "app_dir", lambda: str(cfg_dir))

    con = FakeConsole([])
    cfg, _ = config.ensure(con, non_interactive=True)

    assert cfg["ui_lang"] == "ar"
    assert con.prompts == []
    assert json.loads((cfg_dir / "config.json").read_text(encoding="utf-8"))["ui_lang"] == "ar"


def test_first_run_wizard_starts_with_language_and_saves_it(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "ytdub"
    monkeypatch.setattr(config, "app_dir", lambda: str(cfg_dir))

    con = FakeConsole(["2", "2", "y", "3", "2", "n", "mydl"])
    cfg = config.first_run_wizard(con)

    assert cfg["ui_lang"] == "en"
    assert cfg["ui_theme"] == "midnight"
    assert cfg["max_retries"] == 3 and cfg["retry_wait_seconds"] == 2
    assert cfg["auto_update_check"] is False
    assert cfg["output_dir"] == "mydl"
    assert i18n.get_lang() == "en"
    saved = json.loads((cfg_dir / "config.json").read_text(encoding="utf-8"))
    assert saved["ui_lang"] == "en"


def test_existing_config_missing_theme_uses_default_without_prompt(tmp_path, monkeypatch):
    cfg_dir = tmp_path / "ytdub"
    cfg_dir.mkdir()
    (cfg_dir / "config.json").write_text(json.dumps({"ui_lang": "en", "max_retries": 2}), encoding="utf-8")
    monkeypatch.setattr(config, "app_dir", lambda: str(cfg_dir))

    con = FakeConsole([])
    cfg, _ = config.ensure(con, non_interactive=False)

    assert cfg["ui_theme"] == config.DEFAULTS["ui_theme"] == "classic"
    assert cfg["max_retries"] == 2
    assert con.prompts == []
    saved = json.loads((cfg_dir / "config.json").read_text(encoding="utf-8"))
    assert saved.get("ui_theme", "classic") == "classic" and saved["max_retries"] == 2
