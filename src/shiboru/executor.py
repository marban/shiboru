import sys
from pathlib import Path

from shiboru.constants import FORMAT_ALIASES
from shiboru.errors import OperationError, ToolNotFoundError
from shiboru.models import FileType, Job, OutputMode, Result, Status
from shiboru.optimizers.base import Optimizer
from shiboru.output_writer import compute_output_path, write_result
from shiboru.reporting import print_dry_run_result, print_result, print_summary
from shiboru.scanner import scan
from shiboru.tempdirs import JobTempDir


def run(args) -> int:
    """Main execution entry point. Returns the process exit code."""

    output_mode = OutputMode.REPLACE if args.replace else OutputMode.SUFFIX
    suffix = args.suffix if not args.replace else ""

    allowed_types: set[FileType] | None = None
    if args.formats:
        allowed_types = {FORMAT_ALIASES[f] for f in args.formats}

    jobs = scan(
        args.paths,
        recursive=args.recursive,
        include_hidden=args.include_hidden,
        allowed_types=allowed_types,
    )

    if not jobs:
        print("No supported image files found.", file=sys.stderr)
        return 0

    registry = _build_registry()
    results: list[Result] = []

    for job in jobs:
        if args.dry_run:
            output_path = compute_output_path(
                job.input_path,
                output_mode=output_mode,
                suffix=suffix,
            )
            print_dry_run_result(job, output_path)
            continue

        result = _process_job(
            job=job,
            output_mode=output_mode,
            suffix=suffix,
            registry=registry,
        )
        results.append(result)
        print_result(result, quiet=args.quiet, verbose=args.verbose)

    if not args.dry_run:
        print_summary(results)

    return 1 if any(r.status == Status.FAILED for r in results) else 0


def _process_job(
    job: Job,
    *,
    output_mode: OutputMode,
    suffix: str,
    registry: dict[FileType, Optimizer],
) -> Result:
    original_size = job.input_path.stat().st_size

    optimizer = registry.get(job.file_type)
    if optimizer is None:
        return _failed(job, original_size, "No optimizer available for this format.")

    if not optimizer.is_available():
        return _failed(
            job,
            original_size,
            f"{job.file_type.value.upper()} optimization unavailable: "
            f"required helper tool not found. Try reinstalling dependencies with Homebrew.",
        )

    with JobTempDir() as tmp:
        try:
            outcome = optimizer.optimize(job.input_path, tmp.path)
        except (OperationError, ToolNotFoundError) as exc:
            return _failed(job, original_size, str(exc))

        if not outcome.changed or outcome.candidate_path is None:
            return Result(
                input_path=job.input_path,
                output_path=None,
                file_type=job.file_type,
                original_size=original_size,
                optimized_size=original_size,
                status=Status.UNCHANGED,
            )

        try:
            final_path = write_result(
                job.input_path,
                outcome.candidate_path,
                output_mode=output_mode,
                suffix=suffix,
            )
        except OperationError as exc:
            return _failed(job, original_size, str(exc))

    return Result(
        input_path=job.input_path,
        output_path=final_path,
        file_type=job.file_type,
        original_size=original_size,
        optimized_size=outcome.optimized_size,
        status=Status.OPTIMIZED,
    )


def _failed(job: Job, original_size: int, message: str) -> Result:
    return Result(
        input_path=job.input_path,
        output_path=None,
        file_type=job.file_type,
        original_size=original_size,
        optimized_size=None,
        status=Status.FAILED,
        message=message,
    )


def _build_registry() -> dict[FileType, Optimizer]:
    from shiboru.optimizers.gif import GifOptimizer
    from shiboru.optimizers.ico import IcoOptimizer
    from shiboru.optimizers.jpeg import JpegOptimizer
    from shiboru.optimizers.png import PngOptimizer
    from shiboru.optimizers.svg import SvgOptimizer

    optimizers: list[Optimizer] = [
        PngOptimizer(),
        JpegOptimizer(),
        GifOptimizer(),
        SvgOptimizer(),
        IcoOptimizer(),
    ]
    return {opt.file_type: opt for opt in optimizers}
