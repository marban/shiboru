import shutil
from pathlib import Path

from shiboru.errors import OperationError, ToolNotFoundError
from shiboru.models import FileType
from shiboru.optimizers.base import OptimizationOutcome, Optimizer
from shiboru.tools.locator import find_tool
from shiboru.tools.runner import run_tool
from shiboru.validators.raster import validate_raster


class JpegOptimizer(Optimizer):
    file_type = FileType.JPEG

    def is_available(self) -> bool:
        try:
            find_tool("jpegoptim")
            return True
        except ToolNotFoundError:
            return False

    def optimize(self, input_path: Path, temp_dir: Path) -> OptimizationOutcome:
        original_size = input_path.stat().st_size
        output_path = temp_dir / input_path.name

        # jpegoptim optimizes in-place, so copy to temp first
        shutil.copy2(input_path, output_path)

        jpegoptim = find_tool("jpegoptim")
        result = run_tool(
            [
                jpegoptim,
                "--strip-exif",  # remove camera / GPS data
                "--strip-iptc",  # remove news metadata
                "--strip-xmp",  # remove Adobe XMP data
                "--strip-com",  # remove comments
                # ICC colour profiles are kept (no --strip-icc / --strip-all)
                "--all-progressive",  # progressive encoding: smaller + better browser loading
                "--quiet",
                str(output_path),
            ]
        )

        if not result.ok:
            raise OperationError(
                f"jpegoptim failed on {input_path.name}: {result.stderr.strip()}"
            )

        validate_raster(output_path, FileType.JPEG)

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
