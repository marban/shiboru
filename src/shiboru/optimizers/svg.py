import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path

from shiboru.errors import OperationError
from shiboru.models import FileType
from shiboru.optimizers.base import OptimizationOutcome, Optimizer
from shiboru.validators.svg import validate_svg

_TRANSLATE_RE = re.compile(
    r"^\s*translate\(\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))(?:[\s,]+([+-]?(?:\d+(?:\.\d+)?|\.\d+)))?\s*\)\s*$"
)


class SvgOptimizer(Optimizer):
    file_type = FileType.SVG

    def optimize(self, input_path: Path, temp_dir: Path) -> OptimizationOutcome:
        from scour.scour import getInOut, parse_args, start  # type: ignore[import]

        original_size = input_path.stat().st_size
        output_path = temp_dir / input_path.name

        options = parse_args([])
        options.infilename = str(input_path)
        options.outfilename = str(output_path)

        # Web-optimised preset.
        # IDs and id-referencing attributes are kept intact because they are
        # commonly targeted by CSS selectors and JavaScript — stripping or
        # shortening them would silently break web app assets.
        options.enable_viewboxing = True
        options.enable_id_stripping = False  # keep: CSS/JS may reference IDs
        options.enable_comment_stripping = True  # strip: comments are dev-only
        options.shorten_ids = False  # keep: would break CSS/JS refs
        options.indent_type = "none"  # remove all whitespace (big win)
        options.indent_depth = 0
        options.strip_xml_prolog = True  # not needed by HTML5 browsers
        options.remove_descriptive_elements = True  # strip <title>, <desc>, <metadata>
        options.strip_xml_space_attribute = True  # xml:space not needed on web

        try:
            (infile, outfile) = getInOut(options)
            try:
                start(options, infile, outfile)
            finally:
                infile.close()
                outfile.close()
        except Exception as exc:
            raise OperationError(f"scour failed on {input_path.name}: {exc}") from exc

        _simplify_inverse_group_translates(output_path)
        validate_svg(output_path)

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


def _simplify_inverse_group_translates(path: Path) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    changed = False

    for parent in root.iter():
        if _local_name(parent.tag) != "g":
            continue

        parent_translate = _parse_translate(parent.get("transform"))
        if parent_translate is None:
            continue

        for child in list(parent):
            if _local_name(child.tag) != "g":
                continue

            child_translate = _parse_translate(child.get("transform"))
            if child_translate is None:
                continue

            if child_translate == (-parent_translate[0], -parent_translate[1]):
                del parent.attrib["transform"]
                del child.attrib["transform"]
                changed = True

    if changed:
        namespace = _namespace_uri(root.tag)
        if namespace is not None:
            ET.register_namespace("", namespace)
        tree.write(path, encoding="utf-8", xml_declaration=False)


def _parse_translate(value: str | None) -> tuple[Decimal, Decimal] | None:
    if not value:
        return None

    match = _TRANSLATE_RE.fullmatch(value)
    if match is None:
        return None

    try:
        x = Decimal(match.group(1))
        y = Decimal(match.group(2) or "0")
    except InvalidOperation:
        return None

    return (x, y)


def _local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[1]
    return tag


def _namespace_uri(tag: str) -> str | None:
    if tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return None
