from pathlib import Path

from shiboru.optimizers.svg import _parse_translate, _simplify_inverse_group_translates


def test_parse_translate_accepts_single_and_pair_values():
    assert _parse_translate("translate(10)") == _parse_translate("translate(10, 0)")
    assert _parse_translate("translate(-173 -238)") == _parse_translate(
        "translate(-173,-238)"
    )


def test_simplify_inverse_group_translates_removes_exact_inverse_pair(tmp_path: Path):
    svg = tmp_path / "icon.svg"
    svg.write_text(
        (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g id="outer" transform="translate(-173 -238)">'
            '<g id="inner" transform="translate(173 238)">'
            '<path d="M0 0"/>'
            "</g>"
            "</g>"
            "</svg>"
        ),
        encoding="utf-8",
    )

    _simplify_inverse_group_translates(svg)

    content = svg.read_text(encoding="utf-8")
    assert 'transform="translate(-173 -238)"' not in content
    assert 'transform="translate(173 238)"' not in content
    assert 'id="outer"' in content
    assert 'id="inner"' in content


def test_simplify_inverse_group_translates_keeps_non_inverse_pair(tmp_path: Path):
    svg = tmp_path / "icon.svg"
    svg.write_text(
        (
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<g transform="translate(-173 -238)">'
            '<g transform="translate(173 200)">'
            '<path d="M0 0"/>'
            "</g>"
            "</g>"
            "</svg>"
        ),
        encoding="utf-8",
    )

    _simplify_inverse_group_translates(svg)

    content = svg.read_text(encoding="utf-8")
    assert 'transform="translate(-173 -238)"' in content
    assert 'transform="translate(173 200)"' in content
