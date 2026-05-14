"""Tests for validator.parser — YAML parser with ruamel.yaml line number support."""
import os
import tempfile
import textwrap

import pytest

from validator.parser import ParseError, ParseResult, parse_costformation

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VALID_BASIC = os.path.join(FIXTURES_DIR, "valid_basic.yaml")


# ---------------------------------------------------------------------------
# 1. parse_valid_file
# ---------------------------------------------------------------------------

def test_parse_valid_file():
    result = parse_costformation(VALID_BASIC)
    assert isinstance(result, ParseResult)
    assert "Environment" in result.dimensions


# ---------------------------------------------------------------------------
# 2. parse_returns_line_numbers
# ---------------------------------------------------------------------------

def test_parse_returns_line_numbers():
    result = parse_costformation(VALID_BASIC)
    env_node = result.dimensions["Environment"]
    line = result.line_of(env_node)
    assert line > 0, f"Expected line > 0, got {line}"


# ---------------------------------------------------------------------------
# 3. parse_invalid_yaml_raises
# ---------------------------------------------------------------------------

def test_parse_invalid_yaml_raises():
    bad_yaml = textwrap.dedent("""\
        Dimensions:
          Environment:
            Name: [unclosed bracket
    """)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(bad_yaml)
        tmp_path = f.name
    try:
        with pytest.raises(ParseError):
            parse_costformation(tmp_path)
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# 4. parse_extracts_dimension_ids
# ---------------------------------------------------------------------------

def test_parse_extracts_dimension_ids():
    result = parse_costformation(VALID_BASIC)
    assert set(result.dimensions.keys()) == {"Environment"}


# ---------------------------------------------------------------------------
# 5. parse_returns_raw_text
# ---------------------------------------------------------------------------

def test_parse_returns_raw_text():
    result = parse_costformation(VALID_BASIC)
    assert "Environment" in result.raw_text


# ---------------------------------------------------------------------------
# 6. standalone_detection_for_non_pattern_path
# ---------------------------------------------------------------------------

def test_standalone_detection_for_non_pattern_path():
    # VALID_BASIC is under tests/fixtures/, NOT examples/patterns/
    result = parse_costformation(VALID_BASIC)
    assert result.standalone is False


# ---------------------------------------------------------------------------
# 7. standalone_detection_for_pattern_file
# ---------------------------------------------------------------------------

def test_standalone_detection_for_pattern_file():
    # Construct a temp file whose path contains examples/patterns/
    pattern_dir = os.path.join(tempfile.gettempdir(), "examples", "patterns")
    os.makedirs(pattern_dir, exist_ok=True)
    pattern_file = os.path.join(pattern_dir, "test_pattern.yaml")
    # Copy valid_basic content so it parses cleanly
    with open(VALID_BASIC) as src, open(pattern_file, "w") as dst:
        dst.write(src.read())
    try:
        result = parse_costformation(pattern_file)
        assert result.standalone is True, (
            f"Expected standalone=True for path containing 'examples/patterns/', "
            f"got standalone={result.standalone} for path={pattern_file}"
        )
    finally:
        os.unlink(pattern_file)
