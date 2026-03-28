import pytest

from shiboru.cli import parse_args
from shiboru.constants import DEFAULT_SUFFIX
from shiboru.errors import UsageError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def args_for(tmp_path, *extra):
    """Return parse_args output for a single real file plus any extra flags."""
    f = tmp_path / "img.png"
    f.touch()
    return parse_args([str(f), *extra])


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def test_default_suffix(tmp_path):
    args = args_for(tmp_path)
    assert args.suffix == DEFAULT_SUFFIX


def test_default_replace_is_false(tmp_path):
    args = args_for(tmp_path)
    assert args.replace is False


def test_default_recursive_is_false(tmp_path):
    args = args_for(tmp_path)
    assert args.recursive is False


def test_default_quiet_is_false(tmp_path):
    args = args_for(tmp_path)
    assert args.quiet is False


def test_default_verbose_is_false(tmp_path):
    args = args_for(tmp_path)
    assert args.verbose is False


def test_default_dry_run_is_false(tmp_path):
    args = args_for(tmp_path)
    assert args.dry_run is False


def test_default_formats_is_none(tmp_path):
    args = args_for(tmp_path)
    assert args.formats is None


def test_default_include_hidden_is_false(tmp_path):
    args = args_for(tmp_path)
    assert args.include_hidden is False


# ---------------------------------------------------------------------------
# Path arguments
# ---------------------------------------------------------------------------


def test_single_path(tmp_path):
    f = tmp_path / "a.png"
    f.touch()
    args = parse_args([str(f)])
    assert len(args.paths) == 1


def test_multiple_paths(tmp_path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.jpg"
    a.touch()
    b.touch()
    args = parse_args([str(a), str(b)])
    assert len(args.paths) == 2


def test_no_paths_exits(tmp_path):
    with pytest.raises(SystemExit):
        parse_args([])


# ---------------------------------------------------------------------------
# --replace
# ---------------------------------------------------------------------------


def test_replace_flag(tmp_path):
    args = args_for(tmp_path, "--replace")
    assert args.replace is True


# ---------------------------------------------------------------------------
# --suffix
# ---------------------------------------------------------------------------


def test_custom_suffix(tmp_path):
    args = args_for(tmp_path, "--suffix=-min")
    assert args.suffix == "-min"


def test_suffix_is_stripped_of_whitespace(tmp_path):
    args = args_for(tmp_path, "--suffix=  -min  ")
    assert args.suffix == "-min"


def test_empty_suffix_raises(tmp_path):
    with pytest.raises(UsageError, match="empty"):
        args_for(tmp_path, "--suffix=")


def test_whitespace_only_suffix_raises(tmp_path):
    with pytest.raises(UsageError, match="empty"):
        args_for(tmp_path, "--suffix=   ")


def test_suffix_with_forward_slash_raises(tmp_path):
    with pytest.raises(UsageError, match="path separator"):
        args_for(tmp_path, "--suffix=/bad")


def test_suffix_with_backslash_raises(tmp_path):
    with pytest.raises(UsageError, match="path separator"):
        args_for(tmp_path, r"--suffix=\bad")


# --replace should make suffix validation irrelevant
def test_replace_ignores_suffix_validation(tmp_path):
    # Even with no suffix provided, --replace should not raise
    args = args_for(tmp_path, "--replace")
    assert args.replace is True


# ---------------------------------------------------------------------------
# --recursive / -r
# ---------------------------------------------------------------------------


def test_recursive_long(tmp_path):
    args = args_for(tmp_path, "--recursive")
    assert args.recursive is True


def test_recursive_short(tmp_path):
    args = args_for(tmp_path, "-r")
    assert args.recursive is True


# ---------------------------------------------------------------------------
# --quiet / --verbose
# ---------------------------------------------------------------------------


def test_quiet_long(tmp_path):
    args = args_for(tmp_path, "--quiet")
    assert args.quiet is True


def test_quiet_short(tmp_path):
    args = args_for(tmp_path, "-q")
    assert args.quiet is True


def test_verbose_long(tmp_path):
    args = args_for(tmp_path, "--verbose")
    assert args.verbose is True


def test_verbose_short(tmp_path):
    args = args_for(tmp_path, "-v")
    assert args.verbose is True


def test_quiet_and_verbose_together_raises(tmp_path):
    with pytest.raises(UsageError, match="cannot be used together"):
        args_for(tmp_path, "--quiet", "--verbose")


# ---------------------------------------------------------------------------
# --dry-run / -n
# ---------------------------------------------------------------------------


def test_dry_run_long(tmp_path):
    args = args_for(tmp_path, "--dry-run")
    assert args.dry_run is True


def test_dry_run_short(tmp_path):
    args = args_for(tmp_path, "-n")
    assert args.dry_run is True


# ---------------------------------------------------------------------------
# --formats
# ---------------------------------------------------------------------------


def test_formats_single(tmp_path):
    args = args_for(tmp_path, "--formats=png")
    assert "png" in args.formats


def test_formats_multiple(tmp_path):
    args = args_for(tmp_path, "--formats=png,jpg")
    assert "png" in args.formats
    assert "jpg" in args.formats


def test_formats_jpeg_alias(tmp_path):
    args = args_for(tmp_path, "--formats=jpeg")
    assert "jpeg" in args.formats


def test_formats_all_supported(tmp_path):
    args = args_for(tmp_path, "--formats=png,jpg,jpeg,gif,svg,ico")
    assert len(args.formats) == 6


def test_formats_unknown_raises(tmp_path):
    with pytest.raises(UsageError, match="Unknown format"):
        args_for(tmp_path, "--formats=webp")


def test_formats_mixed_known_unknown_raises(tmp_path):
    with pytest.raises(UsageError, match="Unknown format"):
        args_for(tmp_path, "--formats=png,webp")


def test_formats_empty_raises(tmp_path):
    with pytest.raises(UsageError):
        args_for(tmp_path, "--formats=")


def test_formats_dot_prefix_stripped(tmp_path):
    # Users might type .png instead of png
    args = args_for(tmp_path, "--formats=.png")
    assert "png" in args.formats


# ---------------------------------------------------------------------------
# --include-hidden
# ---------------------------------------------------------------------------


def test_include_hidden(tmp_path):
    args = args_for(tmp_path, "--include-hidden")
    assert args.include_hidden is True
