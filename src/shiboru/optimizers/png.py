import shutil
from pathlib import Path

from shiboru.errors import OperationError, ToolNotFoundError
from shiboru.models import FileType
from shiboru.optimizers.base import OptimizationOutcome, Optimizer
from shiboru.tools.locator import find_tool
from shiboru.tools.runner import run_tool
from shiboru.validators.raster import validate_raster


class PngOptimizer(Optimizer):
    file_type = FileType.PNG

    def is_available(self) -> bool:
        try:
            find_tool("oxipng")
            return True
        except ToolNotFoundError:
            return False

    def optimize(self, input_path: Path, temp_dir: Path) -> OptimizationOutcome:
        original_size = input_path.stat().st_size
        output_path = temp_dir / input_path.name

        # oxipng optimises in-place, so copy first to avoid touching the original.
        shutil.copy2(input_path, output_path)

        oxipng = find_tool("oxipng")
        result = run_tool(
            [
                oxipng,
                "--opt",
                "4",  # more thorough than default 2; still fast enough for web builds
                "--strip",
                "safe",  # strips EXIF/text chunks, keeps ICC colour profiles
                "--alpha",  # set RGB of fully-transparent pixels to 0 — free compression win
                "--interlace",
                "0",  # disable Adam7 interlacing (interlaced PNGs are larger, not smaller)
                "--quiet",
                output_path,
            ]
        )

        if not result.ok:
            raise OperationError(
                f"oxipng failed on {input_path.name}: {result.stderr.strip()}"
            )

        validate_raster(output_path, FileType.PNG)

        optimized_size = output_path.stat().st_size

        if optimized_size >= original_size:
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
