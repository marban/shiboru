from pathlib import Path

from shiboru.models import FileType

# Binary magic byte signatures mapped to FileType.
# Checked in order; first match wins.
_SIGNATURES: list[tuple[bytes, FileType]] = [
    (b"\x89PNG\r\n\x1a\n", FileType.PNG),
    (b"\xff\xd8\xff", FileType.JPEG),
    (b"GIF87a", FileType.GIF),
    (b"GIF89a", FileType.GIF),
    (b"\x00\x00\x01\x00", FileType.ICO),
]

# Extension-based fallback for formats with no binary signature (SVG)
# and as a last resort for ambiguous reads.
_EXTENSION_FALLBACK: dict[str, FileType] = {
    ".png": FileType.PNG,
    ".jpg": FileType.JPEG,
    ".jpeg": FileType.JPEG,
    ".gif": FileType.GIF,
    ".svg": FileType.SVG,
    ".ico": FileType.ICO,
}


def classify(path: Path) -> FileType | None:
    """Return the FileType for path, or None if unsupported or unreadable.

    Resolution order:
      1. Binary magic bytes (reliable, extension-independent).
      2. SVG content sniffing for .svg files (no binary signature exists).
      3. Extension fallback for any remaining ambiguous cases.
    """
    try:
        with path.open("rb") as f:
            header = f.read(16)
    except OSError:
        return None

    # 1. Magic bytes
    for signature, file_type in _SIGNATURES:
        if header.startswith(signature):
            return file_type

    # 2. SVG: no binary signature; detect by extension then confirm via content
    if path.suffix.lower() == ".svg":
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            if "<svg" in text:
                return FileType.SVG
        except OSError:
            pass

    # 3. Extension fallback
    return _EXTENSION_FALLBACK.get(path.suffix.lower())
