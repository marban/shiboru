from pathlib import Path

import pytest

from shiboru.classifier import classify
from shiboru.models import FileType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
_JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 12
_GIF87_HEADER = b"GIF87a" + b"\x00" * 10
_GIF89_HEADER = b"GIF89a" + b"\x00" * 10
_ICO_HEADER = b"\x00\x00\x01\x00" + b"\x00" * 12
_SVG_CONTENT = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"></svg>'


def _write(tmp_path: Path, name: str, content: bytes) -> Path:
    p = tmp_path / name
    p.write_bytes(content)
    return p


# ---------------------------------------------------------------------------
# Magic byte detection
# ---------------------------------------------------------------------------


def test_png_magic(tmp_path):
    p = _write(tmp_path, "image.png", _PNG_HEADER)
    assert classify(p) == FileType.PNG


def test_jpeg_magic(tmp_path):
    p = _write(tmp_path, "photo.jpg", _JPEG_HEADER)
    assert classify(p) == FileType.JPEG


def test_jpeg_magic_with_jpeg_extension(tmp_path):
    p = _write(tmp_path, "photo.jpeg", _JPEG_HEADER)
    assert classify(p) == FileType.JPEG


def test_gif87_magic(tmp_path):
    p = _write(tmp_path, "anim.gif", _GIF87_HEADER)
    assert classify(p) == FileType.GIF


def test_gif89_magic(tmp_path):
    p = _write(tmp_path, "anim.gif", _GIF89_HEADER)
    assert classify(p) == FileType.GIF


def test_ico_magic(tmp_path):
    p = _write(tmp_path, "icon.ico", _ICO_HEADER)
    assert classify(p) == FileType.ICO


# ---------------------------------------------------------------------------
# SVG content sniffing
# ---------------------------------------------------------------------------


def test_svg_by_content(tmp_path):
    p = tmp_path / "icon.svg"
    p.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
    assert classify(p) == FileType.SVG


def test_svg_multiline(tmp_path):
    p = tmp_path / "icon.svg"
    p.write_text(
        '<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg">\n</svg>',
        encoding="utf-8",
    )
    assert classify(p) == FileType.SVG


def test_svg_wrong_extension_not_detected(tmp_path):
    # Content has <svg but extension is not .svg — should not be classified
    p = _write(tmp_path, "icon.txt", _SVG_CONTENT)
    assert classify(p) is None


def test_svg_correct_extension_but_no_svg_tag(tmp_path):
    p = tmp_path / "broken.svg"
    p.write_text("this is not an svg file", encoding="utf-8")
    # Falls through to extension fallback
    assert classify(p) == FileType.SVG


# ---------------------------------------------------------------------------
# Extension fallback
# ---------------------------------------------------------------------------


def test_png_extension_fallback(tmp_path):
    # Unrecognised bytes but .png extension
    p = _write(tmp_path, "weird.png", b"\x00" * 16)
    assert classify(p) == FileType.PNG


def test_jpg_extension_fallback(tmp_path):
    p = _write(tmp_path, "weird.jpg", b"\x00" * 16)
    assert classify(p) == FileType.JPEG


# ---------------------------------------------------------------------------
# Unsupported / unreadable
# ---------------------------------------------------------------------------


def test_unsupported_extension(tmp_path):
    p = _write(tmp_path, "doc.txt", b"hello world")
    assert classify(p) is None


def test_unsupported_binary(tmp_path):
    p = _write(tmp_path, "archive.zip", b"PK\x03\x04" + b"\x00" * 12)
    assert classify(p) is None


def test_missing_file(tmp_path):
    p = tmp_path / "ghost.png"
    assert classify(p) is None


def test_empty_file_falls_back_to_extension(tmp_path):
    p = _write(tmp_path, "empty.png", b"")
    # No magic bytes, but .png extension matches fallback
    assert classify(p) == FileType.PNG
