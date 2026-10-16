"""الفحص والتحديث الذاتي للأدوات (yt-dlp وبقيتها) عند كل تشغيل.

- يقارن النسخة المثبتة مع PyPI عبر importlib.metadata + urllib (مهلة قصيرة).
- يعمل بصمت عند غياب الشبكة — لا يعطل الأداة أبدًا.
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from importlib import metadata

PACKAGES = ["yt-dlp", "rich", "click", "questionary"]
PYPI_TIMEOUT = 8


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


def run_startup_check(console, cfg: dict) -> None:
    """يفحص عند التشغيل: يعرض ثم يحدّث حسب الإعدادات. لا يرفع استثناء أبدًا."""
    if not cfg.get("auto_update_check"):
        return
    try:
        results = check_updates()
    except Exception:
        return
    pending = [r for r in results if r["outdated"]]
    if not pending:
        return
    if cfg.get("auto_update_install"):
        for r in pending:
            console.print(f"🔄 تحديث {r['package']}: {r['installed']} → {r['latest']} ...")
            ok = upgrade(r["package"])
            console.print(
                f"[green]✅ تم تحديث {r['package']}[/green]" if ok else f"[red]❌ فشل تحديث {r['package']}[/red]"
            )
    else:
        names = ", ".join(f"{r['package']} ({r['latest']})" for r in pending)
        console.print(f"[yellow]🔔 تحديثات متاحة: {names}[/yellow]")
