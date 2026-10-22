"""منطق الاختيار الذكي: مطابقة الدبلجة المفضلة وترقية الجودة.

منفصل عن `cli.py` حتى تبقى قواعد الاختيار قابلة للاختبار دون طرفية أو شبكة.
"""

from __future__ import annotations

from .models import DubTrack, Quality

PICK_EXACT = "exact"
PICK_UPGRADED = "upgraded"
PICK_CAPPED = "capped"
PICK_NONE = "none"


def find_dub(dubs: list[DubTrack], lang: str | None) -> DubTrack | None:
    """يبحث عن الدبلجة المفضلة بمقارنة كود اللغة دون حساسية لحالة الأحرف."""
    if not lang:
        return None
    wanted = str(lang).strip().lower()
    return next((d for d in dubs if d.lang.lower() == wanted), None)


def pick_quality(quals: list[Quality], target_height: int | None) -> tuple[Quality | None, str]:
    """يختار الجودة المطلوبة، وإلا أقرب جودة أعلى، وإلا الأعلى المتاحة."""
    if target_height is None or not quals:
        return None, PICK_NONE

    exact = next((q for q in quals if q.height == target_height), None)
    if exact is not None:
        return exact, PICK_EXACT

    higher = sorted((q for q in quals if q.height > target_height), key=lambda q: q.height)
    if higher:
        return higher[0], PICK_UPGRADED

    highest = max(quals, key=lambda q: q.height)
    return highest, PICK_CAPPED
