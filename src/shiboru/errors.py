class ShiboruError(Exception):
    """Base error for shiboru."""


class UsageError(ShiboruError):
    """Bad arguments or usage. Exit code 2."""


class OperationError(ShiboruError):
    """Operational failure. Exit code 1."""


class ToolNotFoundError(OperationError):
    """A required helper binary is not available."""

    def __init__(self, tool: str) -> None:
        self.tool = tool
        super().__init__(
            f"Helper tool '{tool}' not found. "
            f"Try reinstalling dependencies with Homebrew."
        )
