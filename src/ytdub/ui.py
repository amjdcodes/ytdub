"""عرض Rich + اختيار questionary (مع بديل input) + تصاميم متجاوبة.

التصاميم بيانات في `themes.py`، وتُطبّق هنا على Console واحد مشترك حتى
يبدّل المستخدم التصميم أثناء التشغيل دون إعادة بناء الواجهة. كل الجداول
تتكيف مع عرض الطرفية (compact / regular / wide) وتُقصّ عند حدّ مريح للعين.
"""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.progress import BarColumn, DownloadColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from rich.table import Table
from rich.theme import Theme

from . import __version__
from .i18n import SYM_DOT, SYM_SECTION, t
from .models import DubTrack, Quality, VideoInfo
from .themes import (
    DEFAULT_THEME,
    THEME_BOX,
    THEME_NAMES,
    THEME_CLASSIC,
    normalize_theme,
    palette,
    theme_description,
    theme_label,
)
from .utils import format_bytes, format_duration, kind_label

# حدّ أقصى مريح للقراءة على الشاشات العريضة (لا يتمدّد النص إلى ما لا نهاية).
MAX_CONTENT_WIDTH = 110
_COMPACT_BREAK = 62
_WIDE_BREAK = 96
_BOXES = {"round": box.ROUNDED, "square": box.SQUARE}

_ACTIVE_THEME = DEFAULT_THEME
_THEME_PUSHED = False


def _build_theme(name: str) -> Theme:
    return Theme(palette(name), inherit=True)


console = Console(theme=_build_theme(DEFAULT_THEME))


def get_theme() -> str:
    """اسم التصميم النشط حاليًا."""
    return _ACTIVE_THEME


def set_theme(name: str | None) -> str:
    """يبدّل تصميم الواجهة فورًا (دون فقدان أي طباعة سابقة)."""
    global _ACTIVE_THEME, _THEME_PUSHED
    chosen = normalize_theme(name)
    if chosen == _ACTIVE_THEME and _THEME_PUSHED:
        return chosen
    if _THEME_PUSHED:
        console.pop_theme()
        _THEME_PUSHED = False
    console.push_theme(_build_theme(chosen))
    _THEME_PUSHED = True
    _ACTIVE_THEME = chosen
    return chosen


def content_width() -> int:
    """عرض المحتوى المستهدف: يحترم عرض الطرفية ويتوقف عند حدّ قراءة مريح."""
    try:
        width = int(console.size.width or 80)
    except (AttributeError, OSError, ValueError):
        width = 80
    return max(24, min(width, MAX_CONTENT_WIDTH))


def layout(width: int | None = None) -> str:
    """يصنّف الأبعاد: compact (<62) / regular (<96) / wide."""
    w = width if width is not None else content_width()
    if w < _COMPACT_BREAK:
        return "compact"
    if w < _WIDE_BREAK:
        return "regular"
    return "wide"


def _make_table(title: str) -> Table:
    width = content_width()
    return Table(
        title=title,
        box=_BOXES.get(THEME_BOX.get(_ACTIVE_THEME, "round"), box.ROUNDED),
        border_style="table.border",
        header_style="table.header",
        title_style="table.title",
        expand=False,
        pad_edge=False,
        show_lines=False,
        width=width,
        min_width=min(width, 46),
    )


def _kbps(track: DubTrack) -> str:
    return f"{track.abr:.0f}k" if track.abr else "—"


def show_banner() -> None:
    """ترويسة قصيرة تعرض الإصدار والتصميم النشط (تفاعلي فقط)."""
    if not console.is_terminal:
        return
    title = f"[banner.title]{SYM_SECTION} ytdub[/] [muted]v{__version__}[/] [muted]{SYM_DOT}[/] [accent]{theme_label(_ACTIVE_THEME)}[/]"
    console.print(
        Panel(
            f"[banner.subtitle]{t('banner.tagline')}[/]",
            title=title,
            title_align="left",
            border_style="banner.border",
            padding=(0, 1),
            width=content_width(),
        )
    )


def show_video_info(info: VideoInfo) -> None:
    sub = t("video.subtitle", uploader=escape(info.uploader), duration=format_duration(info.duration))
    if info.view_count:
        sub += " " + SYM_DOT + " " + t("video.views", count=info.view_count)
    if content_width() < 50:
        # على الشاشات الضيقة يُعرض العنوان داخل اللوحة حتى يلتف كاملًا.
        body = f"[heading]{SYM_SECTION} {escape(info.title)}[/heading]\n[text]{sub}[/text]"
        title = None
    else:
        body = f"[text]{sub}[/text]"
        title = f"{SYM_SECTION} {escape(info.title)}"
    console.print(
        Panel(
            body,
            title=title,
            title_align="left",
            border_style="panel.border",
            padding=(0, 1),
            width=content_width(),
        )
    )


def show_dubs_table(tracks: list[DubTrack]) -> None:
    if len(tracks) <= 1:
        lang = tracks[0].lang if tracks else "—"
        console.print(f"[warning]{t('dubs.single', lang=lang)}[/warning]")
        return

    mode = layout()
    include_kind = not (mode == "compact" and content_width() < 34)
    t_obj = _make_table(t("dubs.title", count=len(tracks)))
    t_obj.add_column(t("dubs.col_num"), justify="center", style="table.num")
    t_obj.add_column(t("dubs.col_lang"), style="table.row")
    if mode != "compact":
        t_obj.add_column(t("dubs.col_code"), style="table.row")
    if include_kind:
        t_obj.add_column(t("dubs.col_kind"), style="table.row")
    t_obj.add_column(t("dubs.col_quality"), justify="right", style="table.row")

    for d in tracks:
        cells = [str(d.index), d.display]
        if mode != "compact":
            cells.append(d.lang)
        if include_kind:
            cells.append(kind_label(d.kind))
        cells.append(_kbps(d))
        t_obj.add_row(*cells)
    console.print(t_obj)


def show_qualities_table(quals: list[Quality]) -> None:
    mode = layout()
    include_fps = mode == "wide" and any(q.fps for q in quals)
    include_codec = mode == "wide"
    include_note = mode != "compact" and any(q.note for q in quals)

    t_obj = _make_table(t("quals.title", count=len(quals)))
    t_obj.add_column(t("quals.col_num"), justify="center", style="table.num")
    t_obj.add_column(t("quals.col_res"), style="table.row")
    if include_fps:
        t_obj.add_column(t("quals.col_fps"), justify="center", style="table.row")
    if include_codec:
        t_obj.add_column(t("quals.col_codec"), style="table.row")
    t_obj.add_column(t("quals.col_size"), justify="right", style="table.row")
    if include_note:
        t_obj.add_column(t("quals.col_note"), style="table.row")

    for q in quals:
        cells = [str(q.index), f"{q.height}p"]
        if include_fps:
            cells.append(str(q.fps) if q.fps else "—")
        if include_codec:
            cells.append(q.vcodec or "—")
        cells.append(f"~{format_bytes(q.size_approx)}" if q.size_approx else "—")
        if include_note:
            cells.append(q.note)
        t_obj.add_row(*cells)

    audio = ["0", t("quals.audio_row")]
    if include_fps:
        audio.append("—")
    if include_codec:
        audio.append("m4a")
    audio.append("—")
    if include_note:
        audio.append("")
    t_obj.add_row(*audio)
    console.print(t_obj)


def show_estimate(size: int | None, container: str) -> None:
    """يعرض الحجم المتوقع قبل التنزيل (تقديري)."""
    if not size:
        return
    console.print(t("estimate.line", size=f"[accent]~{format_bytes(size)}[/accent]", container=container))


def confirm_overwrite(path: str) -> bool:
    """يسأل عن إعادة تنزيل ملف موجود. يرجع True لإعادة التنزيل (الافتراضي: لا)."""
    prompt = t("confirm.overwrite", path=escape(path))
    while True:
        try:
            raw = console.input(prompt).strip().lower()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError(t("error.input_cancelled"))
        if raw == "":
            return False
        if raw in ("y", "yes", "نعم", "ن"):
            return True
        if raw in ("n", "no", "لا", "ل"):
            return False
        console.print(f"[error]{t('wizard.invalid_yesno')}[/error]")


def _questionary_style():
    """نمط questionary مطابق للتصميم (الكلاسيكي يبقى على نمطه الافتراضي)."""
    if _ACTIVE_THEME == THEME_CLASSIC:
        return None
    try:
        from questionary import Style  # type: ignore

        p = palette(_ACTIVE_THEME)
        return Style(
            [
                ("qmark", f"fg:{p['accent']} bold"),
                ("question", f"fg:{p['text']} bold"),
                ("pointer", f"fg:{p['accent']} bold"),
                ("highlighted", f"fg:{p['accent']} bold"),
                ("selected", f"fg:{p['success']}"),
                ("answer", f"fg:{p['accent']} bold"),
                ("separator", f"fg:{p['muted']}"),
                ("instruction", f"fg:{p['muted']}"),
            ]
        )
    except Exception:
        return None


def _questionary_choices(items: list[str]) -> int | None:
    try:
        import questionary  # type: ignore

        style = _questionary_style()
        kwargs = {"style": style} if style is not None else {}
        ans = questionary.select(t("ask.choose"), choices=[f"{i + 1}. {s}" for i, s in enumerate(items)], **kwargs).ask()
        if ans is None:
            return None
        return int(ans.split(".", 1)[0])
    except ImportError:
        return None
    except Exception:
        return None


def ask_number(prompt: str, minimum: int, maximum: int, default: int) -> int:
    """يسأل برقم مع تحقق؛ Enter = الافتراضي."""
    while True:
        line = t("ask.number_prompt", prompt=prompt, default=default, min=minimum, max=maximum)
        try:
            raw = console.input(line).strip()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError(t("error.input_cancelled"))
        if raw == "":
            return default
        try:
            v = int(raw)
        except ValueError:
            console.print(f"[error]{t('ask.invalid_int')}[/error]")
            continue
        if minimum <= v <= maximum:
            return v
        console.print(f"[error]{t('ask.out_of_range', min=minimum, max=maximum)}[/error]")


def ask_dub(tracks: list[DubTrack]) -> DubTrack:
    if len(tracks) == 1:
        return tracks[0]
    labels = [f"{d.display} ({d.lang}) — {kind_label(d.kind)}" for d in tracks]
    sel = _questionary_choices(labels)
    if sel is not None:
        return tracks[sel - 1]
    default = next((d.index for d in tracks if d.is_default), 1)
    n = ask_number(t("ask.dub_prompt"), 1, len(tracks), default)
    return tracks[n - 1]


def ask_quality(quals: list[Quality]):
    """يرجع (Quality | None, audio_only: bool)."""
    labels = [f"{q.height}p ({q.vcodec}) {q.note}".strip() for q in quals] + [t("quals.audio_row")]
    sel = _questionary_choices(labels)
    if sel is not None:
        if sel == len(quals) + 1:
            return None, True
        return quals[sel - 1], False
    # بديل الأرقام: 0 = صوت فقط
    default = next((q.index for q in quals if q.height == 1080), quals[0].index if quals else 0)
    n = ask_number(t("ask.quality_prompt"), 0, len(quals), default)
    if n == 0:
        return None, True
    return quals[n - 1], False


def ask_theme() -> str | None:
    """قائمة تفاعلية للتصاميم. يرجع اسم التصميم المختار (مطبّق فورًا) أو None."""
    console.print(f"[heading]{t('theme.header')}[/heading]")
    for i, name in enumerate(THEME_NAMES, 1):
        marker = f" [muted]({t('theme.current')})[/muted]" if name == _ACTIVE_THEME else ""
        console.print(f"  [accent]{i}[/accent]) [text]{theme_label(name)}[/text] [muted]— {theme_description(name)}[/muted]{marker}")
    default = THEME_NAMES.index(_ACTIVE_THEME) + 1 if _ACTIVE_THEME in THEME_NAMES else 1
    maximum = len(THEME_NAMES)
    while True:
        try:
            raw = console.input(t("theme.prompt", max=maximum, default=default)).strip().lower()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError(t("error.input_cancelled"))
        if raw in ("", "0"):
            return None
        if raw in THEME_NAMES:
            chosen = raw
        else:
            try:
                n = int(raw)
            except ValueError:
                console.print(f"[error]{t('theme.invalid', max=maximum)}[/error]")
                continue
            if not 1 <= n <= maximum:
                console.print(f"[error]{t('theme.invalid', max=maximum)}[/error]")
                continue
            chosen = THEME_NAMES[n - 1]
        set_theme(chosen)
        return chosen


def show_theme_preview() -> None:
    """معاينة حقيقية للتصميم: لوحة + جدولا الدبلجة والجودة + تقدير الحجم."""
    info = VideoInfo(
        video_id="preview",
        title=t("theme.preview_video"),
        uploader="ytdub",
        duration=754,
        view_count=1250000,
    )
    dubs = [
        DubTrack(1, "ar", "العربية", "dubbed", abr=128.0),
        DubTrack(2, "en", "English", "original", is_default=True, abr=160.0),
        DubTrack(3, "es", "Español", "auto-dub", abr=96.0),
    ]
    quals = [
        Quality(1, 2160, 60, "av01", 3_400_000_000, note=t("quals.note_modern")),
        Quality(2, 1080, 60, "avc1", 1_100_000_000, note=t("quals.note_recommended")),
        Quality(3, 720, 30, "avc1", 520_000_000),
    ]
    show_video_info(info)
    show_dubs_table(dubs)
    show_qualities_table(quals)
    show_estimate(1_100_000_000 + 16_000_000, "mp4")


def make_progress() -> Progress:
    return Progress(
        SpinnerColumn(style="progress.spinner"),
        TextColumn("{task.description}", style="progress.description"),
        BarColumn(
            style="progress.back",
            complete_style="progress.bar",
            finished_style="progress.finished",
            pulse_style="progress.pulse",
        ),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style="progress.percentage"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    )
