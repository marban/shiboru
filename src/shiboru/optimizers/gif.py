from pathlib import Path

from shiboru.errors import OperationError, ToolNotFoundError
from shiboru.models import FileType
from shiboru.optimizers.base import OptimizationOutcome, Optimizer
from shiboru.tools.locator import find_tool
from shiboru.tools.runner import run_tool
from shiboru.validators.raster import validate_raster


class GifOptimizer(Optimizer):
    file_type = FileType.GIF

    def is_available(self) -> bool:
        try:
            find_tool("gifsicle")
            return True
        except ToolNotFoundError:
            return False

    def optimize(self, input_path: Path, temp_dir: Path) -> OptimizationOutcome:
        original_size = input_path.stat().st_size
        output_path = temp_dir / input_path.name

        gifsicle = find_tool("gifsicle")
        result = run_tool(
            [
                gifsicle,
                "-O3",
                "--output",
                output_path,
                input_path,
            ]
        )

        if not result.ok:
            raise OperationError(
                f"gifsicle failed on {input_path.name}: {result.stderr.strip()}"
            )

        validate_raster(output_path, FileType.GIF)

        optimized_size = output_path.stat().st_size
        changed = optimized_size < original_size

        if not changed:
            return OptimizationOutcome(
                candidate_path=None,
                original_size=original_size,
                optimized_size=original_size,
                changed=False,
            )

        return OptimizationOutcome(
            candidate_path=output_path,
            original_size=original_size,
            optimized_size=optimized_size,
            changed=True,
        )
