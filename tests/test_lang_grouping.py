import json
import os

from ytdub.youtube import group_dubs

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "sample_info.json")


def _formats():
    with open(FIX, encoding="utf-8") as f:
        return json.load(f)["formats"]


def test_group_dubs_count_and_order():
    dubs = group_dubs(_formats())
    assert [d.lang for d in dubs] == ["ar", "en", "es"]
    assert dubs[0].kind == "original" and dubs[0].is_default
    assert dubs[2].kind == "auto-dub"


def test_single_lang_becomes_original():
    fmts = [f for f in _formats() if (f.get("language") or "") == "ar"]
    dubs = group_dubs(fmts)
    assert len(dubs) == 1 and dubs[0].is_default


def test_group_dubs_reads_audio_size():
    fmts = [{"acodec": "mp4a.40.2", "vcodec": "none", "language": "ar", "format_note": "original", "abr": 128, "filesize": 4_000_000}]
    dubs = group_dubs(fmts)
    assert dubs[0].size_approx == 4_000_000
