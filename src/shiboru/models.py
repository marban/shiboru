from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class OutputMode(str, Enum):
    REPLACE = "replace"
    SUFFIX = "suffix"


class FileType(str, Enum):
    PNG = "png"
    JPEG = "jpeg"
    GIF = "gif"
    SVG = "svg"
    ICO = "ico"


class Status(str, Enum):
    OPTIMIZED = "optimized"
    UNCHANGED = "unchanged"
    FAILED = "failed"


@dataclass
class Job:
    input_path: Path
    file_type: FileType


@dataclass
class Result:
    input_path: Path
    output_path: Path | None
    file_type: FileType
    original_size: int
    optimized_size: int | None
    status: Status
    message: str | None = None

    @property
    def saved_bytes(self) -> int:
        if self.status != Status.OPTIMIZED or self.optimized_size is None:
            return 0
        return max(0, self.original_size - self.optimized_size)

    @property
    def saved_percent(self) -> float:
        if self.original_size == 0 or self.optimized_size is None:
            return 0.0
        return (self.saved_bytes / self.original_size) * 100
