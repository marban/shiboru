import os
import shutil
from pathlib import Path

from shiboru.constants import HOMEBREW_PREFIXES
from shiboru.errors import ToolNotFoundError

# Simple in-process cache so repeated calls don't re-scan PATH every time.
_cache: dict[str, Path] = {}


def find_tool(name: str) -> Path:
    """Locate a helper binary and return its absolute path.

    Resolution order:
      1. SHIBORU_<NAME>_PATH environment variable (e.g. SHIBORU_OXIPNG_PATH).
      2. shutil.which() — respects the caller's PATH.
      3. Well-known Homebrew prefix directories.

    Raises ToolNotFoundError if the binary cannot be found.
    """
    if name in _cache:
        return _cache[name]

    path = _from_env(name) or _from_which(name) or _from_homebrew(name)

    if path is None:
        raise ToolNotFoundError(name)

    _cache[name] = path
    return path


def clear_cache() -> None:
    """Clear the resolution cache.  Useful in tests."""
    _cache.clear()


# ---------------------------------------------------------------------------
# Resolution strategies
# ---------------------------------------------------------------------------


def _from_env(name: str) -> Path | None:
    """Check for an explicit environment variable override.

    Variable name: SHIBORU_<UPPERCASE_NAME>_PATH
    Example: SHIBORU_OXIPNG_PATH=/usr/local/bin/oxipng
    """
    var = f"SHIBORU_{name.upper().replace('-', '_')}_PATH"
    value = os.environ.get(var)
    if not value:
        return None
    p = Path(value)
    if p.is_file() and os.access(p, os.X_OK):
        return p
    return None


def _from_which(name: str) -> Path | None:
    """Look up the binary using shutil.which (honours the process PATH)."""
    found = shutil.which(name)
    return Path(found) if found else None


def _from_homebrew(name: str) -> Path | None:
    """Check well-known Homebrew binary directories directly."""
    for prefix in HOMEBREW_PREFIXES:
        candidate = Path(prefix) / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None
