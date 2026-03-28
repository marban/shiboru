import struct
from pathlib import Path

import pytest

from shiboru.models import FileType
from shiboru.scanner import scan

# Minimal valid magic bytes for each supported format
_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
_JPEG = b"\xff\xd8\xff" + b"\x00" * 13
_GIF = b"GIF89a" + b"\x00" * 10
_ICO = b"\x00\x00\x01\x00" + b"\x00" * 12
_SVG = b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'


def _write(directory: Path, name: str, content: bytes) -> Path:
    p = directory / name
    p.write_bytes(content)
    return p


# ---------------------------------------------------------------------------
# Single file inputs
# ---------------------------------------------------------------------------


def test_single_png_file(tmp_path):
    f = _write(tmp_path, "logo.png", _PNG)
    jobs = scan([f])
    assert len(jobs) == 1
    assert jobs[0].file_type == FileType.PNG
    assert jobs[0].input_path == f


def test_single_jpeg_file(tmp_path):
    f = _write(tmp_path, "photo.jpg", _JPEG)
    jobs = scan([f])
    assert len(jobs) == 1
    assert jobs[0].file_type == FileType.JPEG


def test_single_gif_file(tmp_path):
    f = _write(tmp_path, "anim.gif", _GIF)
    jobs = scan([f])
    assert len(jobs) == 1
    assert jobs[0].file_type == FileType.GIF


def test_single_svg_file(tmp_path):
    f = _write(tmp_path, "icon.svg", _SVG)
    jobs = scan([f])
    assert len(jobs) == 1
    assert jobs[0].file_type == FileType.SVG


def test_single_ico_file(tmp_path):
    f = _write(tmp_path, "favicon.ico", _ICO)
    jobs = scan([f])
    assert len(jobs) == 1
    assert jobs[0].file_type == FileType.ICO


def test_unsupported_file_skipped(tmp_path):
    f = _write(tmp_path, "readme.txt", b"hello")
    jobs = scan([f])
    assert jobs == []


def test_missing_path_skipped(tmp_path):
    missing = tmp_path / "does_not_exist.png"
    jobs = scan([missing])
    assert jobs == []


# ---------------------------------------------------------------------------
# Multiple file inputs
# ---------------------------------------------------------------------------


def test_multiple_files(tmp_path):
    a = _write(tmp_path, "a.png", _PNG)
    b = _write(tmp_path, "b.jpg", _JPEG)
    jobs = scan([a, b])
    assert len(jobs) == 2
    types = {j.file_type for j in jobs}
    assert FileType.PNG in types
    assert FileType.JPEG in types


def test_order_preserved(tmp_path):
    a = _write(tmp_path, "a.png", _PNG)
    b = _write(tmp_path, "b.png", _PNG)
    c = _write(tmp_path, "c.png", _PNG)
    jobs = scan([a, b, c])
    assert [j.input_path for j in jobs] == [a, b, c]


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def test_same_file_twice_deduplicated(tmp_path):
    f = _write(tmp_path, "logo.png", _PNG)
    jobs = scan([f, f])
    assert len(jobs) == 1


def test_symlink_to_same_file_deduplicated(tmp_path):
    original = _write(tmp_path, "logo.png", _PNG)
    link = tmp_path / "logo_link.png"
    link.symlink_to(original)
    jobs = scan([original, link])
    assert len(jobs) == 1


# ---------------------------------------------------------------------------
# Directory scanning — non-recursive (default)
# ---------------------------------------------------------------------------


def test_directory_immediate_files_only(tmp_path):
    _write(tmp_path, "a.png", _PNG)
    sub = tmp_path / "sub"
    sub.mkdir()
    _write(sub, "b.png", _PNG)

    jobs = scan([tmp_path])
    names = {j.input_path.name for j in jobs}
    assert "a.png" in names
    assert "b.png" not in names


def test_directory_skips_unsupported(tmp_path):
    _write(tmp_path, "notes.txt", b"hello")
    _write(tmp_path, "logo.png", _PNG)

    jobs = scan([tmp_path])
    assert len(jobs) == 1
    assert jobs[0].input_path.name == "logo.png"


# ---------------------------------------------------------------------------
# Directory scanning — recursive
# ---------------------------------------------------------------------------


def test_recursive_finds_nested_files(tmp_path):
    _write(tmp_path, "top.png", _PNG)
    sub = tmp_path / "assets" / "icons"
    sub.mkdir(parents=True)
    _write(sub, "deep.png", _PNG)

    jobs = scan([tmp_path], recursive=True)
    names = {j.input_path.name for j in jobs}
    assert "top.png" in names
    assert "deep.png" in names


def test_recursive_mixed_formats(tmp_path):
    _write(tmp_path, "logo.png", _PNG)
    sub = tmp_path / "sub"
    sub.mkdir()
    _write(sub, "photo.jpg", _JPEG)
    _write(sub, "icon.svg", _SVG)

    jobs = scan([tmp_path], recursive=True)
    types = {j.file_type for j in jobs}
    assert FileType.PNG in types
    assert FileType.JPEG in types
    assert FileType.SVG in types


# ---------------------------------------------------------------------------
# Hidden file policy
# ---------------------------------------------------------------------------


def test_hidden_files_excluded_by_default(tmp_path):
    _write(tmp_path, ".hidden.png", _PNG)
    _write(tmp_path, "visible.png", _PNG)

    jobs = scan([tmp_path])
    names = {j.input_path.name for j in jobs}
    assert "visible.png" in names
    assert ".hidden.png" not in names


def test_hidden_files_included_with_flag(tmp_path):
    _write(tmp_path, ".hidden.png", _PNG)
    _write(tmp_path, "visible.png", _PNG)

    jobs = scan([tmp_path], include_hidden=True)
    names = {j.input_path.name for j in jobs}
    assert "visible.png" in names
    assert ".hidden.png" in names


def test_hidden_directory_excluded_by_default(tmp_path):
    hidden_dir = tmp_path / ".cache"
    hidden_dir.mkdir()
    _write(hidden_dir, "icon.png", _PNG)
    _write(tmp_path, "logo.png", _PNG)

    jobs = scan([tmp_path], recursive=True)
    names = {j.input_path.name for j in jobs}
    assert "logo.png" in names
    assert "icon.png" not in names


def test_hidden_directory_included_with_flag(tmp_path):
    hidden_dir = tmp_path / ".cache"
    hidden_dir.mkdir()
    _write(hidden_dir, "icon.png", _PNG)

    jobs = scan([tmp_path], include_hidden=True, recursive=True)
    names = {j.input_path.name for j in jobs}
    assert "icon.png" in names


# ---------------------------------------------------------------------------
# Format filtering
# ---------------------------------------------------------------------------


def test_allowed_types_filters_out_others(tmp_path):
    _write(tmp_path, "logo.png", _PNG)
    _write(tmp_path, "photo.jpg", _JPEG)

    jobs = scan([tmp_path], allowed_types={FileType.PNG})
    assert all(j.file_type == FileType.PNG for j in jobs)
    assert len(jobs) == 1


def test_allowed_types_empty_set_returns_nothing(tmp_path):
    _write(tmp_path, "logo.png", _PNG)
    jobs = scan([tmp_path], allowed_types=set())
    assert jobs == []


def test_allowed_types_none_returns_all(tmp_path):
    _write(tmp_path, "logo.png", _PNG)
    _write(tmp_path, "photo.jpg", _JPEG)

    jobs = scan([tmp_path], allowed_types=None)
    assert len(jobs) == 2


# ---------------------------------------------------------------------------
# Mixed file and directory inputs
# ---------------------------------------------------------------------------


def test_mixed_file_and_directory_inputs(tmp_path):
    file_a = _write(tmp_path, "a.png", _PNG)
    sub = tmp_path / "sub"
    sub.mkdir()
    _write(sub, "b.png", _PNG)

    jobs = scan([file_a, sub])
    names = {j.input_path.name for j in jobs}
    assert "a.png" in names
    assert "b.png" in names


def test_file_from_dir_and_explicit_not_duplicated(tmp_path):
    """A file that appears both as an explicit arg and inside a scanned
    directory should only produce one job."""
    f = _write(tmp_path, "logo.png", _PNG)
    jobs = scan([f, tmp_path])
    assert len(jobs) == 1
