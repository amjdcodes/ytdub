"""تفضيلات محلية تتعلّم من اختيارات المستخدم للدبلجة والجودة.

تُخزَّن في `preferences.json` بجانب `config.json`، وتُقرأ بأمان: أي ملف تالف
أو غير قابل للكتابة لا يُسقط التطبيق. التعلّم محلي بالكامل ولا يغادر الجهاز.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from . import config

FILENAME = "preferences.json"


def path() -> str:
    return os.path.join(config.app_dir(), FILENAME)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _empty() -> dict:
    return {
        "langs": {},
        "heights": {},
        "last_lang": None,
        "last_height": None,
        "updated_at": "",
    }


def _counts(raw) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not isinstance(raw, dict):
        return counts
    for key, value in raw.items():
        try:
            count = int(value)
        except (TypeError, ValueError):
            continue
        if count > 0:
            counts[str(key)] = count
    return counts


def _height_counts(raw) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key, count in _counts(raw).items():
        try:
            height = int(key)
        except (TypeError, ValueError):
            continue
        if height > 0:
            counts[str(height)] = counts.get(str(height), 0) + count
    return counts


def load() -> dict:
    """يقرأ التفضيلات مع تطبيع الحقول، ويرجع حالة فارغة عند أي خطأ."""
    target = path()
    if not os.path.exists(target):
        return _empty()
    try:
        with open(target, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError):
        return _empty()
    if not isinstance(raw, dict):
        return _empty()

    langs = _counts(raw.get("langs"))
    heights = _height_counts(raw.get("heights"))

    raw_last_lang = raw.get("last_lang")
    last_lang = str(raw_last_lang) if isinstance(raw_last_lang, str) else None
    if last_lang not in langs:
        last_lang = None

    try:
        last_height = int(raw.get("last_height"))
    except (TypeError, ValueError):
        last_height = None
    if last_height is None or str(last_height) not in heights:
        last_height = None

    return {
        "langs": langs,
        "heights": heights,
        "last_lang": last_lang,
        "last_height": last_height,
        "updated_at": str(raw.get("updated_at") or ""),
    }


def save(data: dict) -> str | None:
    """كتابة ذرّية؛ ترجع المسار أو None إذا تعذّرت الكتابة."""
    target = path()
    tmp = target + ".tmp"
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, target)
        return target
    except OSError:
        return None


def record_choice(lang: str | None = None, height: int | None = None) -> dict:
    """يزيد عدّاد اختيار المستخدم (وليس الاختيار التلقائي)."""
    data = load()
    changed = False

    if lang:
        key = str(lang).strip()
        if key:
            data["langs"][key] = data["langs"].get(key, 0) + 1
            data["last_lang"] = key
            changed = True

    if height:
        try:
            value = int(height)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            key = str(value)
            data["heights"][key] = data["heights"].get(key, 0) + 1
            data["last_height"] = value
            changed = True

    if changed:
        data["updated_at"] = _now()
        save(data)
    return data


def _best(counts: dict[str, int], last) -> str | None:
    if not counts:
        return None
    top = max(counts.values())
    candidates = [key for key, count in counts.items() if count == top]
    last_key = str(last) if last is not None else None
    if last_key in candidates:
        return last_key
    return sorted(candidates)[0]


def preferred_lang() -> str | None:
    data = load()
    return _best(data["langs"], data["last_lang"])


def preferred_height() -> int | None:
    data = load()
    key = _best(data["heights"], data["last_height"])
    return int(key) if key is not None else None


def is_empty() -> bool:
    data = load()
    return not data["langs"] and not data["heights"]


def seed(langs, heights, last_lang=None, last_height=None) -> dict:
    """يملأ التفضيلات من السجل مرة واحدة فقط عندما تكون فارغة."""
    data = load()
    if data["langs"] or data["heights"]:
        return data

    data["langs"] = _counts(langs)
    data["heights"] = _height_counts(heights)
    if last_lang in data["langs"]:
        data["last_lang"] = str(last_lang)
    if last_height is not None and str(last_height) in data["heights"]:
        data["last_height"] = int(last_height)
    if data["langs"] or data["heights"]:
        data["updated_at"] = _now()
        save(data)
    return data
