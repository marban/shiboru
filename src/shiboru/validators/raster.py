from pathlib import Path

from shiboru.errors import OperationError
from shiboru.models import FileType

_SIGNATURES: dict[FileType, bytes] = {
    FileType.PNG: b"\x89PNG\r\n\x1a\n",
    FileType.JPEG: b"\xff\xd8\xff",
    FileType.GIF: b"GIF",
    FileType.ICO: b"\x00\x00\x01\x00",
}


def validate_raster(path: Path, file_type: FileType) -> None:
    """
    Verify that path exists, is non-empty, and starts with the expected
    format signature.  Raises OperationError on any failure.
    """
    if not path.exists():
        raise OperationError(f"Optimized output does not exist: {path}")

    if path.stat().st_size == 0:
        raise OperationError(f"Optimized output is empty: {path}")

    expected = _SIGNATURES.get(file_type)
    if expected is None:
        return

    try:
        with path.open("rb") as f:
            header = f.read(len(expected))
    except OSError as exc:
        raise OperationError(f"Cannot read optimized output {path}: {exc}") from exc

    if not header.startswith(expected):
        raise OperationError(
            f"Optimized output has wrong format signature "
            f"(expected {file_type.value.upper()}): {path}"
        )
