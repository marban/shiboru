import os
from pathlib import Path

import pytest

from shiboru.errors import ToolNotFoundError
from shiboru.tools.locator import clear_cache, find_tool


@pytest.fixture(autouse=True)
def reset_cache():
    clear_cache()
    yield
    clear_cache()


def _make_exe(directory: Path, name: str) -> Path:
    p = directory / name
    p.write_text("#!/bin/sh\n")
    p.chmod(0o755)
    return p


def test_find_via_path(tmp_path, monkeypatch):
    exe = _make_exe(tmp_path, "oxipng")
    monkeypatch.setenv("PATH", str(tmp_path))
    result = find_tool("oxipng")
    assert result == exe


def test_env_override_takes_priority(tmp_path, monkeypatch):
    # A real binary on PATH
    (tmp_path / "on_path").mkdir()
    path_exe = _make_exe(tmp_path / "on_path", "oxipng")

    # A different binary referenced by the env var
    override_dir = tmp_path / "override"
    override_dir.mkdir()
    override_exe = _make_exe(override_dir, "oxipng")

    monkeypatch.setenv("PATH", str(tmp_path / "on_path"))
    monkeypatch.setenv("SHIBORU_OXIPNG_PATH", str(override_exe))

    result = find_tool("oxipng")
    assert result == override_exe
    assert result != path_exe


def test_env_override_ignored_if_not_executable(tmp_path, monkeypatch):
    # Non-executable file as override
    bad = tmp_path / "bad_oxipng"
    bad.write_text("not a real binary")
    bad.chmod(0o644)  # not executable
    monkeypatch.setenv("SHIBORU_OXIPNG_PATH", str(bad))

    # Put the real binary on PATH
    exe = _make_exe(tmp_path, "oxipng")
    monkeypatch.setenv("PATH", str(tmp_path))

    result = find_tool("oxipng")
    assert result == exe


def test_env_override_ignored_if_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("SHIBORU_OXIPNG_PATH", str(tmp_path / "does_not_exist"))
    exe = _make_exe(tmp_path, "oxipng")
    monkeypatch.setenv("PATH", str(tmp_path))

    result = find_tool("oxipng")
    assert result == exe


def test_not_found_raises_tool_not_found_error(monkeypatch):
    monkeypatch.setenv("PATH", "")
    monkeypatch.delenv("SHIBORU_OXIPNG_PATH", raising=False)

    with pytest.raises(ToolNotFoundError) as exc_info:
        find_tool("definitely_not_a_real_tool_xyz123")

    assert "definitely_not_a_real_tool_xyz123" in str(exc_info.value)
    assert exc_info.value.tool == "definitely_not_a_real_tool_xyz123"


def test_result_is_cached(tmp_path, monkeypatch):
    exe = _make_exe(tmp_path, "oxipng")
    monkeypatch.setenv("PATH", str(tmp_path))

    first = find_tool("oxipng")

    # Remove the binary — second call should still succeed via cache
    exe.unlink()
    second = find_tool("oxipng")

    assert first == second


def test_clear_cache_forces_re_resolution(tmp_path, monkeypatch):
    exe = _make_exe(tmp_path, "oxipng")
    monkeypatch.setenv("PATH", str(tmp_path))

    find_tool("oxipng")

    # Remove binary and clear cache — next call should fail
    exe.unlink()
    clear_cache()

    with pytest.raises(ToolNotFoundError):
        find_tool("oxipng")


def test_hyphenated_tool_name_env_var(tmp_path, monkeypatch):
    """Tool names with hyphens should map to underscores in the env var name."""
    exe = _make_exe(tmp_path, "jpeg-tool")
    monkeypatch.setenv("SHIBORU_JPEG_TOOL_PATH", str(exe))
    monkeypatch.setenv("PATH", "")

    result = find_tool("jpeg-tool")
    assert result == exe
