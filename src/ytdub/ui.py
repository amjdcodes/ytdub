"""واجهة العرض بـ Rich + الاختيار بـ questionary (مع بديل input)."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, DownloadColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from rich.table import Table

from .models import DubTrack, Quality, VideoInfo
from .utils import KIND_AR, format_bytes, format_duration

console = Console()


def show_video_info(info: VideoInfo) -> None:
    sub = f"{info.uploader} • المدة {format_duration(info.duration)}"
    if info.view_count:
        sub += f" • {info.view_count:,} مشاهدة"
    console.print(Panel(sub, title=f"🎬 {info.title}", border_style="cyan"))


def show_dubs_table(tracks: list[DubTrack]) -> None:
    if len(tracks) <= 1:
        lang = tracks[0].lang if tracks else "—"
        console.print(f"[yellow]لغة صوتية واحدة فقط (الأصلية: {lang}) — سيتم تخطي اختيار الدبلجة.[/yellow]")
        return
    t = Table(title=f"🎧 الدبلجات المتوفرة ({len(tracks)})", show_lines=False)
    t.add_column("#", justify="center")
    t.add_column("اللغة")
    t.add_column("الكود")
    t.add_column("النوع")
    t.add_column("الجودة", justify="right")
    for d in tracks:
        abr = f"{d.abr:.0f}k" if d.abr else "—"
        t.add_row(str(d.index), d.display, d.lang, KIND_AR.get(d.kind, d.kind), abr)
    console.print(t)


def show_qualities_table(quals: list[Quality]) -> None:
    t = Table(title=f"🎞️ الجودات المتوفرة ({len(quals)})", show_lines=False)
    t.add_column("#", justify="center")
    t.add_column("الدقة")
    t.add_column("FPS", justify="center")
    t.add_column("الكودك")
    t.add_column("الحجم", justify="right")
    t.add_column("ملاحظة")
    for q in quals:
        fps = str(q.fps) if q.fps else "—"
        size = f"~{format_bytes(q.size_approx)}" if q.size_approx else "—"
        t.add_row(str(q.index), f"{q.height}p", fps, q.vcodec or "—", size, q.note)
    t.add_row("0", "صوت فقط 🎵", "—", "m4a", "—", "")
    console.print(t)


def _questionary_choices(items: list[str]) -> int | None:
    try:
        import questionary  # type: ignore

        ans = questionary.select("اختر:", choices=[f"{i + 1}. {s}" for i, s in enumerate(items)]).ask()
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
        try:
            raw = console.input(f"{prompt} [{minimum}-{maximum}] (افتراضي {default}): ").strip()
        except (KeyboardInterrupt, EOFError):
            raise RuntimeError("أُلغي الإدخال.")
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


def ask_dub(tracks: list[DubTrack]) -> DubTrack:
    if len(tracks) == 1:
        return tracks[0]
    labels = [f"{d.display} ({d.lang}) — {KIND_AR.get(d.kind, d.kind)}" for d in tracks]
    sel = _questionary_choices(labels)
    if sel is not None:
        return tracks[sel - 1]
    default = next((d.index for d in tracks if d.is_default), 1)
    n = ask_number("❯ اختر الدبلجة", 1, len(tracks), default)
    return tracks[n - 1]


def ask_quality(quals: list[Quality]):
    """يرجع (Quality | None, audio_only: bool)."""
    labels = [f"{q.height}p ({q.vcodec}) {q.note}".strip() for q in quals] + ["صوت فقط 🎵"]
    sel = _questionary_choices(labels)
    if sel is not None:
        if sel == len(quals) + 1:
            return None, True
        return quals[sel - 1], False
    # بديل الأرقام: 0 = صوت فقط
    default = next((q.index for q in quals if q.height == 1080), quals[0].index if quals else 0)
    n = ask_number("❯ اختر الجودة (0 = صوت فقط)", 0, len(quals), default)
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
