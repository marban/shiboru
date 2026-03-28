import argparse
from pathlib import Path

from shiboru import __version__
from shiboru.constants import DEFAULT_SUFFIX, FORMAT_ALIASES
from shiboru.errors import UsageError


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="shiboru",
        description="Optimize PNG, JPEG, GIF, SVG, and ICO images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  shiboru logo.png\n"
            "  shiboru assets/ --recursive\n"
            "  shiboru assets/ --recursive --replace\n"
            "  shiboru assets/ --recursive --suffix=-min\n"
            "  shiboru assets/ --dry-run\n"
        ),
    )

    parser.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        type=Path,
        help="Files or directories to optimize.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--replace",
        action="store_true",
        default=False,
        help="Replace originals in-place using safe atomic replacement.",
    )

    parser.add_argument(
        "--suffix",
        metavar="VALUE",
        default=DEFAULT_SUFFIX,
        help=(
            f"Suffix inserted before the extension on output files "
            f"(default: {DEFAULT_SUFFIX!r}). Ignored when --replace is set."
        ),
    )

    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        default=False,
        help="Recurse into directories.",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Suppress per-file output; show only the summary.",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Show additional diagnostic information.",
    )

    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        default=False,
        dest="dry_run",
        help="Report intended actions without writing any files.",
    )

    parser.add_argument(
        "--formats",
        metavar="LIST",
        default=None,
        help=(
            "Comma-separated list of formats to process, e.g. 'png,jpg'. "
            "Supported: png, jpg, jpeg, gif, svg, ico."
        ),
    )

    parser.add_argument(
        "--include-hidden",
        action="store_true",
        default=False,
        dest="include_hidden",
        help="Include hidden files and directories when scanning.",
    )

    args = parser.parse_args(argv)
    _validate(args)
    return args


def _validate(args: argparse.Namespace) -> None:
    # --quiet and --verbose are mutually exclusive
    if args.quiet and args.verbose:
        raise UsageError("--quiet and --verbose cannot be used together.")

    # Validate suffix (only relevant when not in replace mode)
    if not args.replace:
        suffix = args.suffix.strip() if args.suffix else ""
        if not suffix:
            raise UsageError(
                "--suffix must not be empty. Use --replace to overwrite originals."
            )
        if "/" in suffix or "\\" in suffix:
            raise UsageError("--suffix must not contain path separators.")
        args.suffix = suffix

    # Validate --formats
    if args.formats is not None:
        requested = [
            f.strip().lower().lstrip(".") for f in args.formats.split(",") if f.strip()
        ]
        if not requested:
            raise UsageError("--formats must not be empty.")
        unknown = [f for f in requested if f not in FORMAT_ALIASES]
        if unknown:
            raise UsageError(
                f"Unknown format(s): {', '.join(unknown)}. "
                f"Supported: {', '.join(sorted(set(FORMAT_ALIASES)))}"
            )
        args.formats = set(requested)
