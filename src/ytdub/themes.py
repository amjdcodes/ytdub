"""لوحات ألوان تصاميم الواجهة — بيانات خالصة بلا استيراد rich.

يستهلكها `ui.py` لبناء `rich.theme.Theme`، ويقرأ منها `config.py` أسماء
التصاميم عند المعالج الأول. المفاتيح دلالية (primary/success/...) حتى
تعمل كل عناصر الواجهة مع أي تصميم دون ألوان مكتوبة في الكود.
"""

from __future__ import annotations

from .i18n import t

THEME_CLASSIC = "classic"
THEME_MIDNIGHT = "midnight"
THEME_SAND = "sand"

THEME_NAMES: tuple[str, ...] = (THEME_CLASSIC, THEME_MIDNIGHT, THEME_SAND)
DEFAULT_THEME = THEME_CLASSIC

_ALIASES = {
    "classic": THEME_CLASSIC,
    "default": THEME_CLASSIC,
    "terminal": THEME_CLASSIC,
    "midnight": THEME_MIDNIGHT,
    "night": THEME_MIDNIGHT,
    "dark": THEME_MIDNIGHT,
    "sand": THEME_SAND,
    "warm": THEME_SAND,
    "light": THEME_SAND,
}

# شكل الإطار لكل تصميم (يُترجم إلى rich.box في ui.py)
THEME_BOX: dict[str, str] = {
    THEME_CLASSIC: "round",
    THEME_MIDNIGHT: "round",
    THEME_SAND: "square",
}

# كل تصميم يعرّف نفس المفاتيح تمامًا — يضمنه tests/test_themes.py.
PALETTES: dict[str, dict[str, str]] = {
    THEME_CLASSIC: {
        # ألوان الطرفية الافتراضية: تتكيف تلقائيًا مع الخلفية الفاتحة والداكنة.
        "text": "default",
        "heading": "bold cyan",
        "subheading": "bold default",
        "muted": "dim",
        "primary": "cyan",
        "accent": "bright_cyan",
        "secondary": "magenta",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "info": "blue",
        "panel.border": "cyan",
        "table.border": "grey37",
        "table.header": "bold cyan",
        "table.title": "bold cyan",
        "table.row": "default",
        "table.num": "dim",
        "path": "default",
        "url": "cyan underline",
        "chip": "bold cyan",
        "banner.border": "cyan",
        "banner.title": "bold cyan",
        "banner.subtitle": "dim",
        "progress.back": "grey30",
        "progress.bar": "cyan",
        "progress.finished": "green",
        "progress.pulse": "bright_cyan",
        "progress.description": "default",
        "progress.percentage": "bold cyan",
        "progress.remaining": "dim",
        "progress.speed": "magenta",
        "progress.spinner": "cyan",
    },
    THEME_MIDNIGHT: {
        # أزرق ليلي هادئ (مستوحى من لوحات الليل) — تباين مريح للخلفيات الداكنة.
        "text": "#c0caf5",
        "heading": "bold #7aa2f7",
        "subheading": "bold #a9b1d6",
        "muted": "#7f8ab0",
        "primary": "#7aa2f7",
        "accent": "#7dcfff",
        "secondary": "#bb9af7",
        "success": "#9ece6a",
        "warning": "#e0af68",
        "error": "#f7768e",
        "info": "#2ac3de",
        "panel.border": "#414868",
        "table.border": "#3b4261",
        "table.header": "bold #7aa2f7",
        "table.title": "bold #c0caf5",
        "table.row": "#c0caf5",
        "table.num": "#7f8ab0",
        "path": "#a9b1d6",
        "url": "#7dcfff underline",
        "chip": "bold #7dcfff",
        "banner.border": "#7aa2f7",
        "banner.title": "bold #7aa2f7",
        "banner.subtitle": "#a9b1d6",
        "progress.back": "#2a2f45",
        "progress.bar": "#7aa2f7",
        "progress.finished": "#9ece6a",
        "progress.pulse": "#7dcfff",
        "progress.description": "#c0caf5",
        "progress.percentage": "bold #7dcfff",
        "progress.remaining": "#7f8ab0",
        "progress.speed": "#bb9af7",
        "progress.spinner": "#7dcfff",
    },
    THEME_SAND: {
        # ألوان دافئة منخفضة الإضاءة الزرقاء — مريحة للخلفيات الفاتحة.
        "text": "#3f3a33",
        "heading": "bold #6b4423",
        "subheading": "bold #5c5245",
        "muted": "#8a7f72",
        "primary": "#9a5b2d",
        "accent": "#b45309",
        "secondary": "#7c6f64",
        "success": "#4d7c0f",
        "warning": "#a16207",
        "error": "#b3261e",
        "info": "#0f766e",
        "panel.border": "#c2a878",
        "table.border": "#cbbf9a",
        "table.header": "bold #9a5b2d",
        "table.title": "bold #6b4423",
        "table.row": "#3f3a33",
        "table.num": "#8a7f72",
        "path": "#5c5245",
        "url": "#0f766e underline",
        "chip": "bold #9a5b2d",
        "banner.border": "#b45309",
        "banner.title": "bold #9a5b2d",
        "banner.subtitle": "#5c5245",
        "progress.back": "#e7dcc3",
        "progress.bar": "#b45309",
        "progress.finished": "#4d7c0f",
        "progress.pulse": "#d97706",
        "progress.description": "#3f3a33",
        "progress.percentage": "bold #9a5b2d",
        "progress.remaining": "#8a7f72",
        "progress.speed": "#0f766e",
        "progress.spinner": "#b45309",
    },
}


def normalize_theme(name: str | None) -> str:
    """يطبّع اسم التصميم (مع مرادفات ودّية)، وأي قيمة غير معروفة ترجع للكلاسيكي."""
    return _ALIASES.get(str(name or "").strip().lower(), DEFAULT_THEME)


def palette(name: str | None) -> dict[str, str]:
    """لوحة ألوان التصميم بعد التطبيع."""
    return PALETTES[normalize_theme(name)]


def theme_label(name: str | None) -> str:
    """اسم التصميم المعروض بلغة الواجهة الحالية."""
    return t(f"theme.{normalize_theme(name)}.name")


def theme_description(name: str | None) -> str:
    """وصف قصير للتصميم بلغة الواجهة الحالية."""
    return t(f"theme.{normalize_theme(name)}.desc")
