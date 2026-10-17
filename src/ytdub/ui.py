"""واجهة العرض بـ Rich + الاختيار بـ questionary (مع بديل input)."""

from __future__ import annotations

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.progress import BarColumn, DownloadColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from rich.table import Table

from .i18n import t
from .models import DubTrack, Quality, VideoInfo
from .utils import format_bytes, format_duration, kind_label

console = Console()


def show_video_info(info: VideoInfo) -> None:
    sub = t("video.subtitle", uploader=escape(info.uploader), duration=format_duration(info.duration))
    if info.view_count:
        sub += " • " + t("video.views", count=info.view_count)
    console.print(Panel(sub, title=f"🎬 {escape(info.title)}", border_style="cyan"))


def show_dubs_table(tracks: list[DubTrack]) -> None:
    if len(tracks) <= 1:
        lang = tracks[0].lang if tracks else "—"
        console.print(f"[yellow]{t('dubs.single', lang=lang)}[/yellow]")
        return
    t_obj = Table(title=t("dubs.title", count=len(tracks)), show_lines=False)
    t_obj.add_column(t("dubs.col_num"), justify="center")
    t_obj.add_column(t("dubs.col_lang"))
    t_obj.add_column(t("dubs.col_code"))
    t_obj.add_column(t("dubs.col_kind"))
    t_obj.add_column(t("dubs.col_quality"), justify="right")
    for d in tracks:
        abr = f"{d.abr:.0f}k" if d.abr else "—"
        t_obj.add_row(str(d.index), d.display, d.lang, kind_label(d.kind), abr)
    console.print(t_obj)


def show_qualities_table(quals: list[Quality]) -> None:
    t_obj = Table(title=t("quals.title", count=len(quals)), show_lines=False)
    t_obj.add_column(t("quals.col_num"), justify="center")
    t_obj.add_column(t("quals.col_res"))
    t_obj.add_column(t("quals.col_fps"), justify="center")
    t_obj.add_column(t("quals.col_codec"))
    t_obj.add_column(t("quals.col_size"), justify="right")
    t_obj.add_column(t("quals.col_note"))
    for q in quals:
        fps = str(q.fps) if q.fps else "—"
        size = f"~{format_bytes(q.size_approx)}" if q.size_approx else "—"
        t_obj.add_row(str(q.index), f"{q.height}p", fps, q.vcodec or "—", size, q.note)
    t_obj.add_row("0", t("quals.audio_row"), "—", "m4a", "—", "")
    console.print(t_obj)


def show_estimate(size: int | None, container: str) -> None:
    """يعرض الحجم المتوقع قبل التنزيل (تقديري)."""
    if not size:
        return
    console.print(t("estimate.line", size=f"[bold]~{format_bytes(size)}[/bold]", container=container))


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
        console.print(f"[red]{t('wizard.invalid_yesno')}[/red]")


def _questionary_choices(items: list[str]) -> int | None:
    try:
        import questionary  # type: ignore

        ans = questionary.select(t("ask.choose"), choices=[f"{i + 1}. {s}" for i, s in enumerate(items)]).ask()
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
            console.print(f"[red]{t('ask.invalid_int')}[/red]")
            continue
        if minimum <= v <= maximum:
            return v
        console.print(f"[red]{t('ask.out_of_range', min=minimum, max=maximum)}[/red]")


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


def make_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    )
