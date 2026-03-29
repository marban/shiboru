import struct
import zlib
from pathlib import Path

from shiboru.errors import OperationError, ToolNotFoundError
from shiboru.models import FileType
from shiboru.optimizers.base import OptimizationOutcome, Optimizer
from shiboru.tools.locator import find_tool
from shiboru.tools.runner import run_tool

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# ICO file header: reserved(H), type(H), count(H)
_HEADER = struct.Struct("<HHH")

# ICO directory entry: width(B), height(B), color_count(B), reserved(B),
#                      planes(H), bit_count(H), bytes_in_res(I), image_offset(I)
_DIR_ENTRY = struct.Struct("<BBBBHHII")

_HEADER_SIZE = _HEADER.size  # 6 bytes
_ENTRY_SIZE = _DIR_ENTRY.size  # 16 bytes
_BITMAPINFOHEADER_SIZE = 40
_BI_RGB = 0


class IcoOptimizer(Optimizer):
    file_type = FileType.ICO

    def is_available(self) -> bool:
        try:
            find_tool("oxipng")
            return True
        except ToolNotFoundError:
            return False

    def optimize(self, input_path: Path, temp_dir: Path) -> OptimizationOutcome:
        original_size = input_path.stat().st_size

        try:
            data = input_path.read_bytes()
        except OSError as exc:
            raise OperationError(f"Cannot read {input_path.name}: {exc}") from exc

        optimized_data = _optimize_ico(data, temp_dir, input_path.name)
        optimized_size = len(optimized_data)

        if optimized_size >= original_size:
            return OptimizationOutcome(
                candidate_path=None,
                original_size=original_size,
                optimized_size=original_size,
                changed=False,
            )

        output_path = temp_dir / input_path.name
        output_path.write_bytes(optimized_data)

        return OptimizationOutcome(
            candidate_path=output_path,
            original_size=original_size,
            optimized_size=optimized_size,
            changed=True,
        )


# ---------------------------------------------------------------------------
# ICO parsing and repacking
# ---------------------------------------------------------------------------


def _optimize_ico(data: bytes, temp_dir: Path, filename: str) -> bytes:
    """Parse an ICO, run oxipng on any embedded PNG frames, and return the
    rebuilt ICO bytes.  BMP-encoded frames are carried through untouched."""
    if len(data) < _HEADER_SIZE:
        raise OperationError(f"File is too small to be a valid ICO: {filename}")

    reserved, type_, count = _HEADER.unpack_from(data, 0)
    if reserved != 0 or type_ != 1:
        raise OperationError(f"Not a valid ICO file (bad header): {filename}")

    dir_end = _HEADER_SIZE + count * _ENTRY_SIZE
    if len(data) < dir_end:
        raise OperationError(f"ICO directory is truncated: {filename}")

    # Parse all directory entries
    entries: list[list] = []
    for i in range(count):
        offset = _HEADER_SIZE + i * _ENTRY_SIZE
        entry = list(_DIR_ENTRY.unpack_from(data, offset))
        entries.append(entry)

    # Extract each image frame
    frames: list[bytes] = []
    for entry in entries:
        img_size: int = entry[6]
        img_offset: int = entry[7]

        if img_offset + img_size > len(data):
            raise OperationError(f"ICO frame data extends past end of file: {filename}")

        frame = data[img_offset : img_offset + img_size]
        frames.append(frame)

    # Convert BMP-backed frames to PNG when possible, then optimise PNG frames.
    optimized_frames: list[bytes] = []
    for i, frame in enumerate(frames):
        normalized = _convert_bmp_frame_to_png(frame) or frame
        if normalized.startswith(_PNG_MAGIC):
            optimized_frames.append(_optimize_png_frame(normalized, temp_dir, i))
            continue
        optimized_frames.append(normalized)

    # Rebuild the ICO file with updated sizes and offsets
    return _repack(count, entries, optimized_frames)


def _optimize_png_frame(png_bytes: bytes, temp_dir: Path, index: int) -> bytes:
    """Write a PNG frame to a temp file, run oxipng, and return the result.

    Falls back to the original bytes if oxipng fails or makes the frame larger.
    """
    tmp = temp_dir / f"_frame_{index}.png"
    tmp.write_bytes(png_bytes)

    try:
        oxipng = find_tool("oxipng")
        result = run_tool(
            [
                oxipng,
                "--opt",
                "4",
                "--strip",
                "safe",
                "--alpha",
                "--interlace",
                "0",
                "--quiet",
                tmp,
            ]
        )
        if result.ok:
            optimized = tmp.read_bytes()
            if len(optimized) < len(png_bytes):
                return optimized
    except Exception:
        pass  # If anything goes wrong, keep the original frame

    return png_bytes


def _convert_bmp_frame_to_png(frame: bytes) -> bytes | None:
    """Convert a BMP/DIB-backed ICO frame to PNG when it is a simple 32-bit icon.

    This intentionally handles only the common uncompressed BGRA case exported
    by design tools. Anything more exotic is left untouched.
    """
    if frame.startswith(_PNG_MAGIC) or len(frame) < _BITMAPINFOHEADER_SIZE:
        return None

    (
        header_size,
        width,
        height_twice,
        planes,
        bit_count,
        compression,
        image_size,
        _xppm,
        _yppm,
        _colors_used,
        _colors_important,
    ) = struct.unpack_from("<IIIHHIIIIII", frame, 0)

    if header_size != _BITMAPINFOHEADER_SIZE or width == 0 or height_twice == 0:
        return None
    if planes != 1 or bit_count != 32 or compression != _BI_RGB:
        return None
    if height_twice % 2 != 0:
        return None

    height = height_twice // 2
    xor_row_size = width * 4
    xor_size = xor_row_size * height
    xor_offset = _BITMAPINFOHEADER_SIZE
    and_row_size = ((width + 31) // 32) * 4
    and_offset = xor_offset + xor_size
    and_size = and_row_size * height

    if len(frame) < and_offset + and_size:
        return None

    xor_bitmap = frame[xor_offset:and_offset]
    and_mask = frame[and_offset : and_offset + and_size]

    raw_rows = bytearray()
    for y in range(height):
        src_y = height - 1 - y  # DIB rows are stored bottom-up
        xor_row = xor_bitmap[src_y * xor_row_size : (src_y + 1) * xor_row_size]
        mask_row = and_mask[src_y * and_row_size : (src_y + 1) * and_row_size]

        raw_rows.append(0)  # PNG filter: none
        for x in range(width):
            pixel = x * 4
            b, g, r, a = xor_row[pixel : pixel + 4]
            if a == 0 and _and_mask_bit(mask_row, x):
                raw_rows.extend((r, g, b, 0))
            else:
                raw_rows.extend((r, g, b, a))

    return _build_png(width, height, bytes(raw_rows))


def _and_mask_bit(mask_row: bytes, x: int) -> int:
    byte = mask_row[x // 8]
    shift = 7 - (x % 8)
    return (byte >> shift) & 1


def _build_png(width: int, height: int, raw_rows: bytes) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw_rows, level=9)
    return b"".join(
        [
            _PNG_MAGIC,
            _png_chunk(b"IHDR", ihdr),
            _png_chunk(b"IDAT", idat),
            _png_chunk(b"IEND", b""),
        ]
    )


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def _repack(count: int, entries: list[list], frames: list[bytes]) -> bytes:
    """Assemble a new ICO file from the (possibly modified) directory entries
    and frame data blobs, recalculating all offsets."""
    # Image data starts immediately after the header and directory
    data_start = _HEADER_SIZE + count * _ENTRY_SIZE

    out = bytearray()

    # Write header
    out += _HEADER.pack(0, 1, count)

    # Write directory with updated bytes_in_res and image_offset
    current_offset = data_start
    for i, entry in enumerate(entries):
        new_entry = list(entry)
        new_entry[6] = len(frames[i])  # bytes_in_res
        new_entry[7] = current_offset  # image_offset
        out += _DIR_ENTRY.pack(*new_entry)
        current_offset += len(frames[i])

    # Write frame data
    for frame in frames:
        out += frame

    return bytes(out)
