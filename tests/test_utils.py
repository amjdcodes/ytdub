import os

import pytest

from ytdub.utils import existing_output, read_batch_file, retry_selection


def test_existing_output_matches_merged_file(tmp_path):
    target = tmp_path / "My Video [abc123].mp4"
    target.write_bytes(b"x")
    assert existing_output(str(tmp_path), "abc123", "mp4") == os.path.join(str(tmp_path), target.name)


def test_existing_output_ignores_part_and_fragments(tmp_path):
    (tmp_path / "V [abc].mp4.part").write_bytes(b"x")
    (tmp_path / "V [abc].f299.mp4").write_bytes(b"x")
    assert existing_output(str(tmp_path), "abc", "mp4") is None
    assert existing_output(str(tmp_path), "abc", "") is None


def test_existing_output_container_mismatch(tmp_path):
    (tmp_path / "V [abc].mkv").write_bytes(b"x")
    assert existing_output(str(tmp_path), "abc", "mp4") is None
    assert existing_output(str(tmp_path), "abc", "mkv") is not None


def test_existing_output_missing_dir(tmp_path):
    assert existing_output(str(tmp_path / "nope"), "abc", "mp4") is None


def test_read_batch_file_skips_blank_and_comments(tmp_path):
    p = tmp_path / "urls.txt"
    p.write_text("# comment\n\nhttps://youtu.be/a\n  https://youtu.be/b  \n", encoding="utf-8")
    assert read_batch_file(str(p)) == ["https://youtu.be/a", "https://youtu.be/b"]


def test_read_batch_file_missing_raises():
    with pytest.raises(RuntimeError):
        read_batch_file("/no/such/file.txt")


def test_retry_selection_variants():
    normal = retry_selection({"lang": "ar", "height": 1080, "container": "mp4"})
    assert normal == {"lang": "ar", "height": 1080, "keep_all_dubs": False, "audio_only": False}

    all_dubs = retry_selection({"lang": "all", "height": None, "container": "mkv"})
    assert all_dubs["keep_all_dubs"] is True and all_dubs["lang"] is None and all_dubs["audio_only"] is False

    audio = retry_selection({"lang": "ar", "height": None, "container": "m4a"})
    assert audio["audio_only"] is True and audio["lang"] == "ar"
