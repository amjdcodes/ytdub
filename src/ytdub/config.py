"""ملف التخصيص config.json + معالج أول تشغيل.

المسار: ~/.config/ytdub/config.json (أو %APPDATA%/ytdub على ويندوز).
يُنشأ بأول تشغيل عبر أسئلة تفاعلية، وبعدها يُقرأ تلقائيًا.
"""

from __future__ import annotations

import json
import os
import platform

DEFAULTS: dict = {
    "resume_on_failure": True,
    "max_retries": 5,
    "retry_wait_seconds": 5,
    "concurrent_fragments": 4,
    "socket_timeout": 30,
    "auto_update_check": True,
    "auto_update_install": True,
    "default_lang": None,
    "default_height": None,
    "output_dir": "downloads",
    "player_client": None,
}

CONFIG_FILENAME = "config.json"


def app_dir() -> str:
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "ytdub")
    return os.path.join(os.path.expanduser("~"), ".config", "ytdub")


def config_path() -> str:
    return os.path.join(app_dir(), CONFIG_FILENAME)


def load() -> tuple[dict, bool]:
    """يرجع (الإعدادات, هل_أُنشئ_الآن). يدمج الناقص مع الافتراضيات."""
    path = config_path()
    if not os.path.exists(path):
        return dict(DEFAULTS), False
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return dict(DEFAULTS), False
    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in data.items() if k in DEFAULTS})
    return cfg, True


def save(cfg: dict) -> str:
    path = config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return path


def _ask_yes_no(console, question: str, default: bool) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        try:
            raw = console.input(f"{question} [{hint}]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError("أُلغي الإعداد.")
        if raw == "":
            return default
        if raw in ("y", "yes", "نعم", "ن"):
            return True
        if raw in ("n", "no", "لا", "ل"):
            return False
        console.print("[red]أجب بـ y أو n.[/red]")


def _ask_int(console, question: str, default: int, minimum: int, maximum: int) -> int:
    while True:
        try:
            raw = console.input(f"{question} (افتراضي {default}): ").strip()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError("أُلغي الإعداد.")
        if raw == "":
            return default
        try:
            v = int(raw)
        except ValueError:
            console.print("[red]أدخل رقمًا صحيحًا.[/red]")
            continue
        if minimum <= v <= maximum:
            return v
        console.print(f"[red]الرقم يجب أن يكون بين {minimum} و {maximum}.[/red]")


def first_run_wizard(console) -> dict:
    """أسئلة أول تشغيل — تُحفظ في config.json."""
    console.print("[bold cyan]⚙️ أول تشغيل — إعداد سريع (مرة واحدة فقط):[/bold cyan]")
    cfg = dict(DEFAULTS)
    cfg["resume_on_failure"] = _ask_yes_no(
        console, "🔁 عند فشل التنزيل، هل يعيد المحاولة مع الاستكمال من حيث توقف؟", True
    )
    if cfg["resume_on_failure"]:
        cfg["max_retries"] = _ask_int(console, "🔢 كم مرة يعيد المحاولة عند الفشل المتكرر؟", 5, 1, 20)
        cfg["retry_wait_seconds"] = _ask_int(console, "⏳ كم ثانية ينتظر بين المحاولات؟", 5, 1, 120)
    cfg["auto_update_check"] = _ask_yes_no(
        console, "🔄 هل يفحص تحديثات الأدوات (yt-dlp...) عند كل تشغيل ويثبتها؟", True
    )
    cfg["auto_update_install"] = cfg["auto_update_check"]
    try:
        raw = console.input("📁 مجلد الحفظ الافتراضي (افتراضي downloads): ").strip()
    except (KeyboardInterrupt, EOFError):
        raise RuntimeError("أُلغي الإعداد.")
    if raw:
        cfg["output_dir"] = raw
    path = save(cfg)
    console.print(f"[green]✅ حُفظت الإعدادات في:[/green] {path}")
    return cfg


def ensure(console, non_interactive: bool = False) -> tuple[dict, str]:
    """يرجع (الإعدادات, المسار). ينشئ الافتراضيات بصمت في الوضع غير التفاعلي."""
    cfg, exists = load()
    if exists:
        return cfg, config_path()
    if non_interactive:
        path = save(cfg)
        return cfg, path
    return first_run_wizard(console), config_path()
