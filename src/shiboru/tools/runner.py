import subprocess
import time
from pathlib import Path


class RunResult:
    def __init__(
        self, returncode: int, stdout: str, stderr: str, elapsed: float
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.elapsed = elapsed

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_tool(args: list[str | Path], *, timeout: float | None = None) -> RunResult:
    """Run an external tool with the given argument list.

    Never builds shell strings — always passes a list directly to the OS.
    stdout and stderr are captured and returned in the RunResult.
    """
    str_args = [str(a) for a in args]
    start = time.monotonic()
    proc = subprocess.run(
        str_args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed = time.monotonic() - start
    return RunResult(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        elapsed=elapsed,
    )
