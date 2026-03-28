from shiboru.models import FileType

# Maps file extensions (lowercase, with dot) to FileType
SUPPORTED_EXTENSIONS: dict[str, FileType] = {
    ".png": FileType.PNG,
    ".jpg": FileType.JPEG,
    ".jpeg": FileType.JPEG,
    ".gif": FileType.GIF,
    ".svg": FileType.SVG,
    ".ico": FileType.ICO,
}

# Maps user-facing format names (no dot, lowercase) to FileType
FORMAT_ALIASES: dict[str, FileType] = {
    "png": FileType.PNG,
    "jpg": FileType.JPEG,
    "jpeg": FileType.JPEG,
    "gif": FileType.GIF,
    "svg": FileType.SVG,
    "ico": FileType.ICO,
}

DEFAULT_SUFFIX = "-optimized"

# Well-known Homebrew binary prefixes, in resolution order
HOMEBREW_PREFIXES = [
    "/opt/homebrew/bin",  # Apple Silicon
    "/usr/local/bin",  # Intel
]
