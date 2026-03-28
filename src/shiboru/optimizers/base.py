from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from shiboru.models import FileType


@dataclass
class OptimizationOutcome:
    """The result of a single optimization attempt.

    candidate_path: path to the optimized file inside the job temp dir,
                    or None if the file was unchanged.
    original_size:  size of the input file in bytes.
    optimized_size: size of the candidate file in bytes, or None if unchanged.
    changed:        True if the optimizer produced a smaller file.
    warnings:       any non-fatal messages the optimizer wants to surface.
    """

    candidate_path: Path | None
    original_size: int
    optimized_size: int | None
    changed: bool
    warnings: list[str] = field(default_factory=list)


class Optimizer(ABC):
    """Interface that every format optimizer must implement."""

    file_type: FileType

    @abstractmethod
    def optimize(self, input_path: Path, temp_dir: Path) -> OptimizationOutcome:
        """Optimize input_path and write the result into temp_dir.

        Must not modify input_path directly.
        Must return an OptimizationOutcome describing what happened.
        """
        ...

    def is_available(self) -> bool:
        """Return True if all required helper tools are reachable.

        Overridden by optimizers that depend on external binaries.
        Pure-Python optimizers (e.g. SVG via scour) leave this as True.
        """
        return True
