from pathlib import Path

from shiboru.errors import OperationError


def validate_svg(path: Path) -> None:
    """
    Verify that path exists, is non-empty, and contains a recognisable SVG root element.
    Raises OperationError on any failure.
    """
    if not path.exists():
        raise OperationError(f"Optimized SVG does not exist: {path}")

    if path.stat().st_size == 0:
        raise OperationError(f"Optimized SVG is empty: {path}")

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise OperationError(f"Cannot read optimized SVG {path}: {exc}") from exc

    if "<svg" not in text:
        raise OperationError(f"Optimized SVG does not contain an <svg> element: {path}")
