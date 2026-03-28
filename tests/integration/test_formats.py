"""
Integration tests — one per supported format.

Generates real fixture files, runs each optimizer, and prints compression ratios.

Usage:
    pytest tests/integration/ -v -s

Requires helper tools to be installed:
    brew install oxipng jpegoptim gifsicle

Requires Pillow for PNG / JPEG / GIF fixture generation:
    pip install Pillow
"""

import io
import struct
import zlib
from pathlib import Path

import pytest

from shiboru.optimizers.gif import GifOptimizer
from shiboru.optimizers.ico import IcoOptimizer
from shiboru.optimizers.jpeg import JpegOptimizer
from shiboru.optimizers.png import PngOptimizer
from shiboru.optimizers.svg import SvgOptimizer
from shiboru.tempdirs import JobTempDir

# ---------------------------------------------------------------------------
# Pillow availability
# ---------------------------------------------------------------------------

try:
    from PIL import Image, ImageDraw  # type: ignore[import]

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

needs_pillow = pytest.mark.skipif(
    not HAS_PILLOW,
    reason="Pillow not installed — run: pip install Pillow",
)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    return f"{n / 1024:.1f} KB"


def _print_result(label: str, original: int, optimized: int | None) -> None:
    bar = "─" * 60
    print(f"\n  {bar}")
    print(f"  {label}")
    print(f"  {bar}")
    if optimized is None or optimized >= original:
        print(f"  original : {_fmt(original)}")
        print(f"  result   : unchanged")
    else:
        saved = original - optimized
        pct = saved / original * 100
        print(f"  original : {_fmt(original)}")
        print(f"  output   : {_fmt(optimized)}")
        print(f"  saved    : {_fmt(saved)}  ({pct:.1f}% smaller)")


# ---------------------------------------------------------------------------
# Fixture generators
# ---------------------------------------------------------------------------


def _make_png(path: Path) -> None:
    """300×300 RGBA gradient saved without optimisation — gives oxipng room to work."""
    img = Image.new("RGBA", (300, 300), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    for x in range(300):
        r = int(x / 300 * 255)
        for y in range(300):
            g = int(y / 300 * 255)
            draw.point((x, y), fill=(r, g, 128, 200))
    # compress_level=1: minimal compression so oxipng has room to improve
    img.save(str(path), "PNG", compress_level=1)


def _make_jpeg(path: Path) -> None:
    """400×300 RGB gradient at quality 95, no progressive, no stripping."""
    img = Image.new("RGB", (400, 300))
    draw = ImageDraw.Draw(img)
    for y in range(300):
        r = int(y / 300 * 255)
        g = 80
        b = int((300 - y) / 300 * 255)
        draw.line([(0, y), (399, y)], fill=(r, g, b))
    img.save(str(path), "JPEG", quality=95, optimize=False, progressive=False)


def _make_gif(path: Path) -> None:
    """10-frame animation — gifsicle can optimise frame differencing."""
    frames = []
    for i in range(10):
        frame = Image.new("RGB", (200, 150), color=(i * 25, 100, 200 - i * 20))
        draw = ImageDraw.Draw(frame)
        # Moving rectangle across frames
        x = i * 15
        draw.rectangle([x, 30, x + 60, 120], fill=(255, 200 - i * 20, i * 25))
        # Convert to palette mode for GIF
        frames.append(frame.convert("P", palette=Image.ADAPTIVE))
    frames[0].save(
        str(path),
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=100,
    )


def _make_svg(path: Path) -> None:
    """
    Verbose SVG with XML declaration, DOCTYPE, comments, <metadata>, and
    heavy indentation — gives scour a lot to strip.
    """
    content = """\
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">

<!-- ============================================================ -->
<!-- Test SVG fixture for shiboru integration tests               -->
<!-- This comment block should be stripped by scour               -->
<!-- ============================================================ -->

<svg
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    version="1.1"
    width="200"
    height="200"
    viewBox="0 0 200 200"
    xml:space="preserve">

    <!-- Metadata block — scour removes this entirely -->
    <metadata>
        <rdf:RDF>
            <rdf:Description rdf:about="">
                <dc:creator>Thomas Marban</dc:creator>
                <dc:title>Test SVG</dc:title>
                <dc:description>Integration test fixture for shiboru</dc:description>
                <dc:date>2025-01-01</dc:date>
            </rdf:Description>
        </rdf:RDF>
    </metadata>

    <!-- Background -->
    <rect
        id="background"
        x="0"
        y="0"
        width="200"
        height="200"
        style="fill:#f0f0f0;stroke:none;" />

    <!-- Main circle -->
    <circle
        id="main-circle"
        cx="100"
        cy="100"
        r="80"
        style="fill:#e63946;stroke:#1d3557;stroke-width:3;" />

    <!-- Inner circle -->
    <circle
        id="inner-circle"
        cx="100"
        cy="100"
        r="50"
        style="fill:#457b9d;stroke:none;opacity:0.8;" />

    <!-- Label -->
    <text
        id="label"
        x="100"
        y="106"
        text-anchor="middle"
        dominant-baseline="middle"
        style="font-family:sans-serif;font-size:20px;font-weight:bold;fill:#f1faee;">
        shiboru
    </text>

    <!-- Decorative corner marks -->
    <g id="corners">
        <line x1="0"   y1="0"   x2="20"  y2="0"   style="stroke:#1d3557;stroke-width:2;" />
        <line x1="0"   y1="0"   x2="0"   y2="20"  style="stroke:#1d3557;stroke-width:2;" />
        <line x1="200" y1="0"   x2="180" y2="0"   style="stroke:#1d3557;stroke-width:2;" />
        <line x1="200" y1="0"   x2="200" y2="20"  style="stroke:#1d3557;stroke-width:2;" />
        <line x1="0"   y1="200" x2="20"  y2="200" style="stroke:#1d3557;stroke-width:2;" />
        <line x1="0"   y1="200" x2="0"   y2="180" style="stroke:#1d3557;stroke-width:2;" />
        <line x1="200" y1="200" x2="180" y2="200" style="stroke:#1d3557;stroke-width:2;" />
        <line x1="200" y1="200" x2="200" y2="180" style="stroke:#1d3557;stroke-width:2;" />
    </g>

</svg>
"""
    path.write_text(content, encoding="utf-8")


def _make_ico(path: Path) -> None:
    """
    ICO with one 64×64 PNG-encoded frame generated in pure Python.
    The embedded PNG is stored uncompressed so oxipng has plenty to do.
    """

    def _chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    size = 64
    # IHDR: width, height, bit depth, color type (2=RGB), compression, filter, interlace
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))

    # IDAT: uncompressed scanlines (filter byte 0 = None + RGB pixels)
    raw_rows = b""
    for y in range(size):
        row = b"\x00"  # filter byte
        for x in range(size):
            r = int(x / size * 255)
            g = int(y / size * 255)
            b_val = 128
            row += bytes([r, g, b_val])
        raw_rows += row
    # level=0 → store, no compression — gives oxipng maximum room to optimise
    idat = _chunk(b"IDAT", zlib.compress(raw_rows, level=0))
    iend = _chunk(b"IEND", b"")

    png_bytes = b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend

    # ICO container: 1 entry pointing at the PNG frame
    header = struct.pack("<HHH", 0, 1, 1)  # reserved, type=1, count=1
    data_offset = 6 + 16  # header + one 16-byte directory entry
    # width=0 means 256; use 0 for sizes ≥256, else actual size
    dir_entry = struct.pack(
        "<BBBBHHII",
        size if size < 256 else 0,  # width
        size if size < 256 else 0,  # height
        0,  # color count (0 = no palette)
        0,  # reserved
        1,  # planes
        24,  # bits per pixel
        len(png_bytes),  # size of image data
        data_offset,  # offset to image data
    )
    path.write_bytes(header + dir_entry + png_bytes)


# ---------------------------------------------------------------------------
# Shared optimizer runner
# ---------------------------------------------------------------------------


def _run(optimizer, fixture_path: Path):
    """Run optimizer and return (original_size, optimized_size | None)."""
    original = fixture_path.stat().st_size
    with JobTempDir() as tmp:
        outcome = optimizer.optimize(fixture_path, tmp.path)
        if outcome.changed and outcome.candidate_path is not None:
            optimized = outcome.candidate_path.stat().st_size
        else:
            optimized = None
    return original, optimized


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@needs_pillow
def test_png(tmp_path):
    optimizer = PngOptimizer()
    if not optimizer.is_available():
        pytest.skip("oxipng not found — brew install oxipng")

    fixture = tmp_path / "test.png"
    _make_png(fixture)

    original, optimized = _run(optimizer, fixture)
    _print_result("PNG  (oxipng --opt 4 --alpha --interlace 0)", original, optimized)

    assert original > 0
    if optimized is not None:
        assert optimized < original


@needs_pillow
def test_jpeg(tmp_path):
    optimizer = JpegOptimizer()
    if not optimizer.is_available():
        pytest.skip("jpegoptim not found — brew install jpegoptim")

    fixture = tmp_path / "test.jpg"
    _make_jpeg(fixture)

    original, optimized = _run(optimizer, fixture)
    _print_result(
        "JPEG (jpegoptim --strip-exif --strip-iptc --strip-xmp --all-progressive)",
        original,
        optimized,
    )

    assert original > 0
    if optimized is not None:
        assert optimized < original


@needs_pillow
def test_gif(tmp_path):
    optimizer = GifOptimizer()
    if not optimizer.is_available():
        pytest.skip("gifsicle not found — brew install gifsicle")

    fixture = tmp_path / "test.gif"
    _make_gif(fixture)

    original, optimized = _run(optimizer, fixture)
    _print_result("GIF  (gifsicle -O3)", original, optimized)

    assert original > 0


def test_svg(tmp_path):
    optimizer = SvgOptimizer()

    fixture = tmp_path / "test.svg"
    _make_svg(fixture)

    original, optimized = _run(optimizer, fixture)
    _print_result(
        "SVG  (scour: strip comments / metadata / whitespace)", original, optimized
    )

    assert original > 0
    if optimized is not None:
        assert optimized < original


def test_ico(tmp_path):
    optimizer = IcoOptimizer()
    if not optimizer.is_available():
        pytest.skip("oxipng not found — brew install oxipng")

    fixture = tmp_path / "test.ico"
    _make_ico(fixture)

    original, optimized = _run(optimizer, fixture)
    _print_result(
        "ICO  (pure-Python parser + oxipng on embedded PNG frames)", original, optimized
    )

    assert original > 0
    if optimized is not None:
        assert optimized < original
