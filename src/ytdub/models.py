"""نماذج البيانات — حسب docs/05-architecture-blueprint.md."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DubTrack:
    index: int
    lang: str  # كود ISO 639-1 مثل "ar"
    display: str  # اسم للعرض مثل "العربية"
    kind: str  # original | dubbed | auto-dub | descriptive | unknown
    is_default: bool = False
    abr: float | None = None
    size_approx: int | None = None
    sample_format_id: str = ""


@dataclass
class Quality:
    index: int
    height: int  # 0 = صوت فقط
    fps: int | None = None
    vcodec: str = ""
    size_approx: int | None = None
    sample_format_id: str = ""
    note: str = ""


@dataclass
class VideoInfo:
    video_id: str
    title: str
    uploader: str = ""
    duration: int | None = None
    view_count: int | None = None
    formats: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)
