"""الفحص والتحديث الذاتي للأدوات (yt-dlp وبقيتها) عند كل تشغيل.

- يقارن النسخة المثبتة مع PyPI عبر importlib.metadata + urllib (مهلة قصيرة).
- يخزّن ختم آخر فحص في state_dir ويتخطى الفحص حتى انقضاء update_check_interval_hours.
- يعمل بصمت عند غياب الشبكة — لا يعطل الأداة أبدًا.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from importlib import metadata

from .i18n import t

PACKAGES = ["yt-dlp", "rich", "click", "questionary"]
PYPI_TIMEOUT = 8
STAMP_FILENAME = "last_update_check"


def _parse_version(v: str) -> tuple:
    parts: list = []
    for p in str(v).replace("-", ".").split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def installed_version(pkg: str) -> str | None:
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return None


def latest_version(pkg: str) -> str | None:
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{pkg}/json", timeout=PYPI_TIMEOUT) as r:
            return json.load(r)["info"]["version"]
    except Exception:
        return None


def check_updates() -> list[dict]:
    """يفحص كل حزمة: {package, installed, latest, outdated}."""
    out = []
    for pkg in PACKAGES:
        inst = installed_version(pkg)
        lat = latest_version(pkg)
        outdated = bool(inst and lat and _parse_version(lat) > _parse_version(inst))
        out.append({"package": pkg, "installed": inst, "latest": lat, "outdated": outdated})
    return out


def _should_check(state_dir: str | None, interval_hours: int) -> bool:
    """يتخطى الفحص إن مرّ أقل من interval_hours على آخر فحص ناجح.

    interval_hours <= 0 يعطّل التخزين المؤقت (فحص كل تشغيل).
    """
    if not state_dir or interval_hours <= 0:
        return True
    stamp = os.path.join(state_dir, STAMP_FILENAME)
    try:
        age = datetime.now(timezone.utc).timestamp() - os.path.getmtime(stamp)
    except OSError:
        return True
    return age >= interval_hours * 3600


def _touch_stamp(state_dir: str | None) -> None:
    """يحدّث ختم آخر فحص — يفشل بصمت عند تعذّر الكتابة."""
    if not state_dir:
        return
    try:
        os.makedirs(state_dir, exist_ok=True)
        stamp = os.path.join(state_dir, STAMP_FILENAME)
        with open(stamp, "w", encoding="utf-8") as f:
            f.write(datetime.now(timezone.utc).isoformat(timespec="seconds"))
    except OSError:
        pass


def upgrade(pkg: str) -> bool:
    """يثبت أحدث نسخة عبر pip — يجرّب ثم بعلامة كسر الحماية عند الحاجة."""
    cmds = [
        [sys.executable, "-m", "pip", "install", "-q", "-U", pkg],
        [sys.executable, "-m", "pip", "install", "-q", "-U", "--break-system-packages", pkg],
    ]
    for cmd in cmds:
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            return True
        except Exception:
            continue
    return False


def run_startup_check(console, cfg: dict, state_dir: str | None = None) -> None:
    """يفحص عند التشغيل: يعرض ثم يحدّث حسب الإعدادات. لا يرفع استثناء أبدًا.

    state_dir يخزّن ختم آخر فحص لتفادي ضرب PyPI كل تشغيل (interval_hours).
    """
    if not cfg.get("auto_update_check"):
        return
    interval = int(cfg.get("update_check_interval_hours", 24) or 0)
    if not _should_check(state_dir, interval):
        return
    try:
        results = check_updates()
    except Exception:
        return
    _touch_stamp(state_dir)
    pending = [r for r in results if r["outdated"]]
    if not pending:
        return
    if cfg.get("auto_update_install"):
        for r in pending:
            console.print(t("update.upgrading", pkg=r["package"], old=r["installed"], new=r["latest"]))
            ok = upgrade(r["package"])
            if ok:
                console.print(f"[green]{t('update.ok', pkg=r['package'])}[/green]")
            else:
                console.print(f"[red]{t('update.fail', pkg=r['package'])}[/red]")
    else:
        names = ", ".join(f"{r['package']} ({r['latest']})" for r in pending)
        console.print(f"[yellow]{t('update.available', names=names)}[/yellow]")
