import sys
from pathlib import Path

from shiboru.models import Job, Result, Status


def format_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.1f} MB"


def print_result(result: Result, *, quiet: bool = False, verbose: bool = False) -> None:
    if quiet:
        return

    name = str(result.input_path)
    fmt = result.file_type.value.upper()

    if result.status == Status.OPTIMIZED:
        orig = format_size(result.original_size)
        opt = format_size(result.optimized_size)  # type: ignore[arg-type]
        pct = f"-{result.saved_percent:.1f}%"
        print(f"{name:<40}  {fmt:<5}  {orig:>8} -> {opt:<8}  {pct}")
        if verbose and result.output_path:
            print(f"  -> {result.output_path}")

    elif result.status == Status.UNCHANGED:
        orig = format_size(result.original_size)
        print(f"{name:<40}  {fmt:<5}  {orig:>8}  (unchanged)")

    elif result.status == Status.FAILED:
        msg = result.message or "unknown error"
        print(f"{name:<40}  {fmt:<5}  FAILED: {msg}", file=sys.stderr)


def print_dry_run_result(job: Job, output_path: Path) -> None:
    name = str(job.input_path)
    fmt = job.file_type.value.upper()
    try:
        size = format_size(job.input_path.stat().st_size)
    except OSError:
        size = "?"
    print(f"{name:<40}  {fmt:<5}  {size:>8}  -> {output_path}  [dry run]")


def print_summary(results: list[Result]) -> None:
    total = len(results)
    optimized = sum(1 for r in results if r.status == Status.OPTIMIZED)
    unchanged = sum(1 for r in results if r.status == Status.UNCHANGED)
    failed = sum(1 for r in results if r.status == Status.FAILED)
    total_saved = sum(r.saved_bytes for r in results)

    print()
    print(f"{total} {'file' if total == 1 else 'files'} processed")
    print(f"{optimized} optimized, {unchanged} unchanged, {failed} failed")
    if total_saved > 0:
        print(f"Total saved: {format_size(total_saved)}")
