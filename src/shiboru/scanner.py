from pathlib import Path

from shiboru.classifier import classify
from shiboru.models import FileType, Job


def scan(
    paths: list[Path],
    *,
    recursive: bool = False,
    include_hidden: bool = False,
    allowed_types: set[FileType] | None = None,
) -> list[Job]:
    """Return a deduplicated, ordered list of Jobs from the given input paths."""
    seen: set[Path] = set()
    jobs: list[Job] = []

    for path in paths:
        if path.is_file():
            _try_add(path, seen, jobs, allowed_types)
        elif path.is_dir():
            _scan_dir(
                path,
                recursive=recursive,
                include_hidden=include_hidden,
                seen=seen,
                jobs=jobs,
                allowed_types=allowed_types,
            )
        # Silently skip paths that are neither file nor directory
        # (missing, special device, etc.). Verbose mode can report these later.

    return jobs


def _try_add(
    path: Path,
    seen: set[Path],
    jobs: list[Job],
    allowed_types: set[FileType] | None,
) -> None:
    try:
        resolved = path.resolve()
    except OSError:
        return

    if resolved in seen:
        return

    file_type = classify(path)
    if file_type is None:
        return
    if allowed_types is not None and file_type not in allowed_types:
        return

    seen.add(resolved)
    jobs.append(Job(input_path=path, file_type=file_type))


def _scan_dir(
    directory: Path,
    *,
    recursive: bool,
    include_hidden: bool,
    seen: set[Path],
    jobs: list[Job],
    allowed_types: set[FileType] | None,
) -> None:
    pattern = "**/*" if recursive else "*"
    for entry in sorted(directory.glob(pattern)):
        if not entry.is_file():
            continue
        if not include_hidden and _has_hidden_component(entry, relative_to=directory):
            continue
        _try_add(entry, seen, jobs, allowed_types)


def _has_hidden_component(path: Path, relative_to: Path) -> bool:
    """Return True if any path component relative to `relative_to` starts with a dot."""
    try:
        rel = path.relative_to(relative_to)
    except ValueError:
        return False
    return any(part.startswith(".") for part in rel.parts)
