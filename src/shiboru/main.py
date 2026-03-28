import sys

from shiboru.cli import parse_args
from shiboru.errors import ShiboruError, UsageError


def main() -> None:
    try:
        args = parse_args()
    except UsageError as exc:
        print(f"shiboru: error: {exc}", file=sys.stderr)
        sys.exit(2)

    from shiboru.executor import run

    try:
        exit_code = run(args)
    except UsageError as exc:
        print(f"shiboru: error: {exc}", file=sys.stderr)
        sys.exit(2)
    except ShiboruError as exc:
        print(f"shiboru: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(1)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
