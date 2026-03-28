from pathlib import Path

import pytest

from shiboru.models import OutputMode
from shiboru.output_writer import compute_output_path


def test_suffix_default(tmp_path):
    f = tmp_path / "logo.png"
    f.touch()
    result = compute_output_path(f, output_mode=OutputMode.SUFFIX, suffix="-optimized")
    assert result.name == "logo-optimized.png"
    assert result.parent == tmp_path


def test_suffix_custom(tmp_path):
    f = tmp_path / "logo.png"
    f.touch()
    result = compute_output_path(f, output_mode=OutputMode.SUFFIX, suffix="-min")
    assert result.name == "logo-min.png"


def test_suffix_preserves_extension_case(tmp_path):
    f = tmp_path / "image.PNG"
    f.touch()
    result = compute_output_path(f, output_mode=OutputMode.SUFFIX, suffix="-optimized")
    assert result.suffix == ".PNG"


def test_suffix_multi_dot_filename(tmp_path):
    # Only the final extension should be preserved; the suffix goes before it.
    f = tmp_path / "logo.min.png"
    f.touch()
    result = compute_output_path(f, output_mode=OutputMode.SUFFIX, suffix="-optimized")
    assert result.name == "logo.min-optimized.png"


def test_replace_returns_input_path(tmp_path):
    f = tmp_path / "logo.png"
    f.touch()
    result = compute_output_path(f, output_mode=OutputMode.REPLACE, suffix="")
    assert result == f


def test_collision_first(tmp_path):
    f = tmp_path / "logo.png"
    f.touch()
    (tmp_path / "logo-optimized.png").touch()

    result = compute_output_path(f, output_mode=OutputMode.SUFFIX, suffix="-optimized")
    assert result.name == "logo-optimized-2.png"


def test_collision_multiple(tmp_path):
    f = tmp_path / "logo.png"
    f.touch()
    (tmp_path / "logo-optimized.png").touch()
    (tmp_path / "logo-optimized-2.png").touch()
    (tmp_path / "logo-optimized-3.png").touch()

    result = compute_output_path(f, output_mode=OutputMode.SUFFIX, suffix="-optimized")
    assert result.name == "logo-optimized-4.png"


def test_no_collision_when_target_absent(tmp_path):
    f = tmp_path / "logo.png"
    f.touch()
    result = compute_output_path(f, output_mode=OutputMode.SUFFIX, suffix="-optimized")
    assert result.name == "logo-optimized.png"
    assert not result.exists()
