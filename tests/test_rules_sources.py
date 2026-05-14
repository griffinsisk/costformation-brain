"""Tests for source rules: prefix validation and unresolved User:Defined refs."""
import os

import pytest

from validator.parser import parse_costformation
from validator.diagnostic import Severity
from validator.rules.sources import SourcePrefixRule, UnresolvedUserDefinedRule

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VALID_BASIC = os.path.join(FIXTURES_DIR, "valid_basic.yaml")
INVALID_SOURCE = os.path.join(FIXTURES_DIR, "invalid_source.yaml")
VALID_STANDALONE = os.path.join(FIXTURES_DIR, "valid_standalone.yaml")


def _context(result):
    return {
        "filename": result.filename,
        "standalone": result.standalone,
        "raw_text": result.raw_text,
        "yaml_obj": result.yaml_obj,
    }


# ---------------------------------------------------------------------------
# SourcePrefixRule
# ---------------------------------------------------------------------------

def test_catches_bare_custom_source():
    result = parse_costformation(INVALID_SOURCE)
    diagnostics = SourcePrefixRule().check(result.dimensions, _context(result))
    prefix_missing = [d for d in diagnostics if d.rule_id == "source-prefix-missing"]
    assert len(prefix_missing) == 1
    assert prefix_missing[0].severity == Severity.ERROR
    assert "Environment" in prefix_missing[0].message
    assert prefix_missing[0].dimension_id == "Bad"


def test_catches_cz_prefix_on_billing_source():
    result = parse_costformation(INVALID_SOURCE)
    diagnostics = SourcePrefixRule().check(result.dimensions, _context(result))
    prefix_wrong = [d for d in diagnostics if d.rule_id == "source-prefix-wrong"]
    assert len(prefix_wrong) == 1
    assert prefix_wrong[0].severity == Severity.ERROR
    assert "Account" in prefix_wrong[0].message
    assert prefix_wrong[0].dimension_id == "Bad"


def test_catches_resourceid():
    result = parse_costformation(INVALID_SOURCE)
    diagnostics = SourcePrefixRule().check(result.dimensions, _context(result))
    resourceid = [d for d in diagnostics if d.rule_id == "source-resourceid"]
    assert len(resourceid) == 1
    assert resourceid[0].severity == Severity.ERROR
    assert "ResourceSummaryDisplay" in resourceid[0].message
    assert resourceid[0].dimension_id == "Bad"


def test_passes_valid_sources():
    result = parse_costformation(VALID_BASIC)
    diagnostics = SourcePrefixRule().check(result.dimensions, _context(result))
    assert diagnostics == []


# ---------------------------------------------------------------------------
# UnresolvedUserDefinedRule
# ---------------------------------------------------------------------------

def test_catches_unresolved_in_full_file():
    result = parse_costformation(VALID_STANDALONE, standalone=False)
    ctx = _context(result)
    ctx["standalone"] = False
    diagnostics = UnresolvedUserDefinedRule().check(result.dimensions, ctx)
    unresolved = [d for d in diagnostics if d.rule_id == "unresolved-user-defined"]
    assert len(unresolved) == 2
    names = {d.message.split("'")[1] for d in unresolved}
    assert names == {"SharedAllocation", "SpendCategory"}


def test_suppressed_for_standalone():
    result = parse_costformation(VALID_STANDALONE, standalone=True)
    ctx = _context(result)
    ctx["standalone"] = True
    diagnostics = UnresolvedUserDefinedRule().check(result.dimensions, ctx)
    assert diagnostics == []


def test_handles_array_source_notation(tmp_path):
    """Source can be a list like [Tag:Application, Tag:application]."""
    fixture = tmp_path / "array_source.yaml"
    fixture.write_text(
        "Dimensions:\n"
        "  App:\n"
        "    Name: Application\n"
        "    Rules:\n"
        "      - Type: GroupBy\n"
        "        Source:\n"
        "          - Tag:Application\n"
        "          - Tag:application\n"
    )
    result = parse_costformation(str(fixture))
    ctx = _context(result)
    prefix_diags = SourcePrefixRule().check(result.dimensions, ctx)
    assert prefix_diags == []
    unresolved_diags = UnresolvedUserDefinedRule().check(result.dimensions, ctx)
    assert unresolved_diags == []
