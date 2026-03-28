import shutil
import tempfile
from pathlib import Path


class JobTempDir:
    """A temporary directory scoped to a single optimization job.

    Use as a context manager to ensure cleanup on exit:

        with JobTempDir() as tmp:
            outcome = optimizer.optimize(input_path, tmp.path)
    """

    def __init__(self) -> None:
        self._dir = tempfile.mkdtemp(prefix="shiboru-")
        self.path = Path(self._dir)

    def cleanup(self) -> None:
        shutil.rmtree(self._dir, ignore_errors=True)

    def __enter__(self) -> "JobTempDir":
        return self

    def __exit__(self, *_: object) -> None:
        self.cleanup()
