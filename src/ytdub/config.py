"""ملف التخصيص config.json + معالج أول تشغيل.

المسار: ~/.config/ytdub/config.json (أو %APPDATA%/ytdub على ويندوز).
يُنشأ بأول تشغيل عبر أسئلة تفاعلية، وبعدها يُقرأ تلقائيًا.
"""

from __future__ import annotations

import json
import os
import platform

from .i18n import LANG_AR, LANG_EN, SYM_PROMPT, set_lang, t
from .themes import DEFAULT_THEME, THEME_NAMES, normalize_theme, theme_description, theme_label

DEFAULTS: dict = {
    "ui_lang": "ar",
    "ui_theme": DEFAULT_THEME,
    "smart_picks": False,
    "resume_on_failure": True,
    "max_retries": 5,
    "retry_wait_seconds": 5,
    "concurrent_fragments": 4,
    "socket_timeout": 30,
    "auto_update_check": True,
    "auto_update_install": True,
    "update_check_interval_hours": 24,
    "default_lang": None,
    "default_height": None,
    "output_dir": "downloads",
    "player_client": None,
    "skip_existing": True,
}

CONFIG_FILENAME = "config.json"


def app_dir() -> str:
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "ytdub")
    return os.path.join(os.path.expanduser("~"), ".config", "ytdub")


def config_path() -> str:
    return os.path.join(app_dir(), CONFIG_FILENAME)


def _read_raw() -> dict:
    """يقرأ محتوى الملف كما هو (بلا دمج افتراضيات) — لاكتشاف المفاتيح الناقصة."""
    path = config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def load() -> tuple[dict, bool]:
    """يرجع (الإعدادات, هل_الملف_موجود). يدمج الناقص مع الافتراضيات."""
    exists = os.path.exists(config_path())
    data = _read_raw()
    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
    return cfg, exists


def save(cfg: dict) -> str:
    path = config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return path


def _ask_language(console) -> str:
    """سؤال اللغة الوحيد — نصّه مزدوج حتى قبل تحديد اللغة."""
    console.print(t("wizard.lang_header"))
    console.print("  1) العربية")
    console.print("  2) English")
    while True:
        try:
            raw = console.input(f"{SYM_PROMPT} [1-2] (1): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError(t("error.setup_cancelled"))
        if raw in ("", "1", "ar", "arabic", "العربية", "ع"):
            return LANG_AR
        if raw in ("2", "en", "english", "eng", "الإنجليزية", "انجليزي", "ا"):
            return LANG_EN
        console.print(t("wizard.lang_invalid"))


def _ask_theme(console) -> str:
    """سؤال التصميم — يُطرح مرة واحدة في المعالج الأول (Enter = الكلاسيكي)."""
    console.print(t("theme.header"))
    for i, name in enumerate(THEME_NAMES, 1):
        console.print(f"  {i}) {theme_label(name)} — {theme_description(name)}")
    maximum = len(THEME_NAMES)
    while True:
        try:
            raw = console.input(t("theme.prompt", max=maximum, default=1)).strip().lower()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError(t("error.setup_cancelled"))
        if raw == "":
            return DEFAULT_THEME
        if raw in THEME_NAMES:
            return normalize_theme(raw)
        try:
            n = int(raw)
        except ValueError:
            console.print(f"[red]{t('theme.invalid', max=maximum)}[/red]")
            continue
        if 1 <= n <= maximum:
            return THEME_NAMES[n - 1]
        console.print(f"[red]{t('theme.invalid', max=maximum)}[/red]")


def _ask_yes_no(console, question: str, default: bool) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        try:
            raw = console.input(f"{question} ({hint}): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError(t("error.setup_cancelled"))
        if raw == "":
            return default
        if raw in ("y", "yes", "نعم", "ن"):
            return True
        if raw in ("n", "no", "لا", "ل"):
            return False
        console.print(f"[red]{t('wizard.invalid_yesno')}[/red]")


def _ask_int(console, question: str, default: int, minimum: int, maximum: int) -> int:
    while True:
        prompt = t("ask.number_prompt", prompt=question, default=default, min=minimum, max=maximum)
        try:
            raw = console.input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError(t("error.setup_cancelled"))
        if raw == "":
            return default
        try:
            v = int(raw)
        except ValueError:
            console.print(f"[red]{t('wizard.invalid_int')}[/red]")
            continue
        if minimum <= v <= maximum:
            return v
        console.print(f"[red]{t('wizard.int_range', min=minimum, max=maximum)}[/red]")


def first_run_wizard(console) -> dict:
    """أسئلة أول تشغيل — تبدأ باللغة ثم بقية الأسئلة بها، وتُحفظ في config.json."""
    lang = _ask_language(console)
    set_lang(lang)
    theme = _ask_theme(console)
    console.print(f"[bold cyan]{t('wizard.intro')}[/bold cyan]")
    cfg = dict(DEFAULTS)
    cfg["ui_lang"] = lang
    cfg["ui_theme"] = theme
    cfg["resume_on_failure"] = _ask_yes_no(console, t("wizard.retry_q"), True)
    if cfg["resume_on_failure"]:
        cfg["max_retries"] = _ask_int(console, t("wizard.retry_max_q"), 5, 1, 20)
        cfg["retry_wait_seconds"] = _ask_int(console, t("wizard.retry_wait_q"), 5, 1, 120)
    cfg["auto_update_check"] = _ask_yes_no(console, t("wizard.update_q"), True)
    cfg["auto_update_install"] = cfg["auto_update_check"]
    cfg["smart_picks"] = _ask_yes_no(console, t("wizard.smart_q"), False)
    try:
        raw = console.input(t("wizard.output_q")).strip()
    except (KeyboardInterrupt, EOFError):
        raise RuntimeError(t("error.setup_cancelled"))
    if raw:
        cfg["output_dir"] = raw
    path = save(cfg)
    console.print(f"[green]{t('wizard.saved', path=path)}[/green]")
    return cfg


def ensure(console, non_interactive: bool = False) -> tuple[dict, str]:
    """يرجع (الإعدادات, المسار) ويضبط لغة الواجهة.

    - ملف غير موجود: معالج كامل (تفاعلي) أو افتراضيات بصمت (غير تفاعلي).
    - ملف موجود: لا يعيد الأسئلة؛ إن كان ينقصه `ui_lang` (إعداد قديم) يسأل عن اللغة فقط.
    """
    if not os.path.exists(config_path()):
        if non_interactive:
            cfg = dict(DEFAULTS)
            path = save(cfg)
            set_lang(cfg["ui_lang"])
            return cfg, path
        cfg = first_run_wizard(console)
        set_lang(cfg["ui_lang"])
        return cfg, config_path()

    raw = _read_raw()
    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in raw.items() if k in DEFAULTS})
    cfg["ui_theme"] = normalize_theme(cfg.get("ui_theme"))

    norm = str(raw.get("ui_lang") or "").strip().lower()
    if norm in (LANG_AR, LANG_EN):
        cfg["ui_lang"] = norm
    else:
        # هجرة خفيفة: السؤال الناقص فقط، دون إعادة كل أسئلة المعالج
        cfg["ui_lang"] = DEFAULTS["ui_lang"] if non_interactive else _ask_language(console)
        save(cfg)

    set_lang(cfg["ui_lang"])
    return cfg, config_path()
