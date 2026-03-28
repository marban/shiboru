import os
import shutil
from pathlib import Path

from shiboru.errors import OperationError
from shiboru.models import OutputMode


def compute_output_path(
    input_path: Path,
    *,
    output_mode: OutputMode,
    suffix: str,
) -> Path:
    """
    Return the intended output path for an input file without writing anything.
    In replace mode this is the input path itself.
    In suffix mode a collision-safe name is computed.
    """
    if output_mode == OutputMode.REPLACE:
        return input_path
    return _suffix_path(input_path, suffix)


def write_result(
    input_path: Path,
    candidate_path: Path,
    *,
    output_mode: OutputMode,
    suffix: str,
) -> Path:
    """
    Move the optimized candidate file into its final destination.
    Returns the path where the file ended up.
    """
    if output_mode == OutputMode.REPLACE:
        return _atomic_replace(candidate_path, input_path)
    output_path = _suffix_path(input_path, suffix)
    _atomic_move(candidate_path, output_path)
    return output_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _suffix_path(input_path: Path, suffix: str) -> Path:
    """
    Compute a suffix-mode output path, incrementing a counter to avoid
    collisions with existing files.

    logo.png -> logo-optimized.png
                logo-optimized-2.png  (if first already exists)
                logo-optimized-3.png  ...
    """
    stem = input_path.stem
    ext = input_path.suffix
    parent = input_path.parent

    candidate = parent / f"{stem}{suffix}{ext}"
    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        candidate = parent / f"{stem}{suffix}-{counter}{ext}"
        if not candidate.exists():
            return candidate
        counter += 1


def _atomic_replace(src: Path, dst: Path) -> Path:
    """
    Safely overwrite dst with src using a sibling temporary file so that
    the final rename is atomic on the same filesystem.

    Algorithm:
      1. Copy src to a hidden sibling temp file next to dst.
      2. os.replace() the sibling onto dst  (atomic on APFS / HFS+).
      3. On any error, clean up the sibling and re-raise.
    """
    sibling = dst.parent / f".shiboru-tmp-{dst.name}"
    try:
        shutil.copy2(src, sibling)
        os.replace(sibling, dst)
    except OSError as exc:
        sibling.unlink(missing_ok=True)
        raise OperationError(f"Failed to replace {dst}: {exc}") from exc
    return dst


def _atomic_move(src: Path, dst: Path) -> None:
    """
    Move src to dst.  Tries os.replace() first (atomic when same filesystem),
    falls back to copy-then-delete for cross-device situations.
    """
    try:
        os.replace(src, dst)
    except OSError:
        try:
            shutil.copy2(src, dst)
            src.unlink(missing_ok=True)
        except OSError as exc:
            raise OperationError(f"Failed to write {dst}: {exc}") from exc
