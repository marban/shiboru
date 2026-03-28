import struct
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

    # Optimise any PNG frames
    optimized_frames: list[bytes] = []
    for i, frame in enumerate(frames):
        if frame.startswith(_PNG_MAGIC):
            optimized_frames.append(_optimize_png_frame(frame, temp_dir, i))
        else:
            optimized_frames.append(frame)

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
