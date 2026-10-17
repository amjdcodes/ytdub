import json
import os

from ytdub.models import DubTrack, Quality
from ytdub.youtube import build_format, estimate_size, group_dubs, group_qualities

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "sample_info.json")


def _load():
    with open(FIX, encoding="utf-8") as f:
        return json.load(f)["formats"]


def test_qualities_dedup_and_sort():
    quals = group_qualities(_load())
    assert [q.height for q in quals] == [2160, 1080, 720]
    assert any("موصى" in q.note for q in quals)


def test_build_format_dub_quality():
    fmts = _load()
    dubs = group_dubs(fmts)
    quals = group_qualities(fmts)
    es = next(d for d in dubs if d.lang == "es")
    q1080 = next(q for q in quals if q.height == 1080)
    fmt, container, _ = build_format(es, q1080)
    assert "language=es" in fmt and "height<=1080" in fmt and container == "mp4"


def test_build_format_keep_all():
    fmt, container, extra = build_format(None, None, keep_all_dubs=True)
    assert container == "mkv" and extra.get("audio_multistreams") is True


def test_build_format_audio_only():
    fmts = _load()
    ar = next(d for d in group_dubs(fmts) if d.lang == "ar")
    fmt, container, _ = build_format(ar, None, audio_only=True)
    assert fmt.startswith("ba[language=ar]")


def _dub(size):
    return DubTrack(index=1, lang="ar", display="العربية", kind="original", size_approx=size)


def test_estimate_size_sums_video_and_audio():
    q = Quality(index=1, height=1080, size_approx=95_000_000)
    assert estimate_size(_dub(5_000_000), q) == 100_000_000


def test_estimate_size_audio_only_and_keep_all():
    assert estimate_size(_dub(5_000_000), None, audio_only=True) == 5_000_000
    assert estimate_size(_dub(5_000_000), None, keep_all_dubs=True) is None


def test_estimate_size_none_without_data():
    assert estimate_size(_dub(None), Quality(index=1, height=720)) is None
