"""Tests for syntax rules: missing-type, groupby-missing-source, unquoted-account-id."""
import os

import pytest

from validator.parser import parse_costformation
from validator.diagnostic import Severity
from validator.rules.syntax import (
    GroupByMissingSourceRule,
    LogicalOperatorListRule,
    MissingTypeRule,
    UnquotedAccountIdRule,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VALID_BASIC = os.path.join(FIXTURES_DIR, "valid_basic.yaml")
INVALID_TYPE = os.path.join(FIXTURES_DIR, "invalid_type.yaml")
INVALID_ACCOUNT_IDS = os.path.join(FIXTURES_DIR, "invalid_account_ids.yaml")
INVALID_GROUPBY_NO_SOURCE = os.path.join(
    FIXTURES_DIR, "invalid_groupby_no_source.yaml"
)
INVALID_NOT_MAPPING = os.path.join(FIXTURES_DIR, "invalid_not_mapping.yaml")


def _context(result):
    return {
        "filename": result.filename,
        "standalone": result.standalone,
        "raw_text": result.raw_text,
        "yaml_obj": result.yaml_obj,
    }


# ---------------------------------------------------------------------------
# LogicalOperatorListRule
# ---------------------------------------------------------------------------

def test_catches_logical_operator_bare_mapping():
    result = parse_costformation(INVALID_NOT_MAPPING)
    diagnostics = LogicalOperatorListRule().check(result.dimensions, _context(result))
    assert len(diagnostics) == 2
    assert {d.rule_id for d in diagnostics} == {"logical-operator-not-list"}
    messages = " ".join(d.message for d in diagnostics)
    assert "'Not'" in messages and "'And'" in messages
    for d in diagnostics:
        assert d.severity == Severity.ERROR
        assert d.dimension_id == "Environment"


def test_logical_operator_rule_passes_valid_file():
    result = parse_costformation(VALID_BASIC)
    diagnostics = LogicalOperatorListRule().check(result.dimensions, _context(result))
    assert diagnostics == []


def test_logical_operator_rule_passes_all_pattern_examples():
    patterns_dir = os.path.join(
        os.path.dirname(__file__), "..", "examples", "patterns"
    )
    for fname in sorted(os.listdir(patterns_dir)):
        if not fname.endswith(".yaml"):
            continue
        result = parse_costformation(os.path.join(patterns_dir, fname))
        diagnostics = LogicalOperatorListRule().check(
            result.dimensions, _context(result)
        )
        assert diagnostics == [], f"bare And/Or/Not mapping in {fname}: {diagnostics}"


# ---------------------------------------------------------------------------
# GroupByMissingSourceRule
# ---------------------------------------------------------------------------

def test_catches_groupby_without_rule_level_source():
    result = parse_costformation(INVALID_GROUPBY_NO_SOURCE)
    diagnostics = GroupByMissingSourceRule().check(result.dimensions, _context(result))
    assert len(diagnostics) == 2
    assert {d.dimension_id for d in diagnostics} == {"Team", "CostCenter"}
    for d in diagnostics:
        assert d.severity == Severity.ERROR
        assert d.rule_id == "groupby-missing-source"


def test_groupby_source_rule_passes_valid_file():
    result = parse_costformation(VALID_BASIC)
    diagnostics = GroupByMissingSourceRule().check(result.dimensions, _context(result))
    assert diagnostics == []


def test_groupby_source_rule_passes_all_pattern_examples():
    patterns_dir = os.path.join(
        os.path.dirname(__file__), "..", "examples", "patterns"
    )
    for fname in sorted(os.listdir(patterns_dir)):
        if not fname.endswith(".yaml"):
            continue
        result = parse_costformation(os.path.join(patterns_dir, fname))
        diagnostics = GroupByMissingSourceRule().check(
            result.dimensions, _context(result)
        )
        assert diagnostics == [], f"bare GroupBy in {fname}: {diagnostics}"


# ---------------------------------------------------------------------------
# MissingTypeRule
# ---------------------------------------------------------------------------

def test_catches_missing_type():
    result = parse_costformation(INVALID_TYPE)
    context = {
        "filename": result.filename,
        "standalone": result.standalone,
        "raw_text": result.raw_text,
        "yaml_obj": result.yaml_obj,
    }
    diagnostics = MissingTypeRule().check(result.dimensions, context)
    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.severity == Severity.ERROR
    assert d.rule_id == "missing-type"
    assert d.dimension_id == "Bad"


def test_missing_type_passes_valid_file():
    result = parse_costformation(VALID_BASIC)
    context = {
        "filename": result.filename,
        "standalone": result.standalone,
        "raw_text": result.raw_text,
        "yaml_obj": result.yaml_obj,
    }
    diagnostics = MissingTypeRule().check(result.dimensions, context)
    assert diagnostics == []


# ---------------------------------------------------------------------------
# UnquotedAccountIdRule
# ---------------------------------------------------------------------------

def test_catches_unquoted_account_id():
    result = parse_costformation(INVALID_ACCOUNT_IDS)
    context = {
        "filename": result.filename,
        "standalone": result.standalone,
        "raw_text": result.raw_text,
        "yaml_obj": result.yaml_obj,
    }
    diagnostics = UnquotedAccountIdRule().check(result.dimensions, context)
    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.severity == Severity.ERROR
    assert d.rule_id == "unquoted-account-id"
    assert "123456789012" in d.message


def test_passes_quoted_ids():
    result = parse_costformation(VALID_BASIC)
    context = {
        "filename": result.filename,
        "standalone": result.standalone,
        "raw_text": result.raw_text,
        "yaml_obj": result.yaml_obj,
    }
    diagnostics = UnquotedAccountIdRule().check(result.dimensions, context)
    assert diagnostics == []


# ---------------------------------------------------------------------------
# UnquotedAccountIdRule — value-position precision (only flag bare YAML values,
# not account IDs embedded in Name labels or free-form text).
# ---------------------------------------------------------------------------

def _raw_ctx(raw_text):
    return {"filename": "t.yaml", "standalone": False,
            "raw_text": raw_text, "yaml_obj": {}}


def test_account_id_in_name_label_not_flagged():
    # IDs inside a Name label are part of a string — no coercion risk.
    raw = ("        Name: Audit (058264478258)\n"
           "        Conditions:\n"
           "          - Equals: '058264478258'\n")
    assert UnquotedAccountIdRule().check({}, _raw_ctx(raw)) == []


def test_unquoted_equals_value_flagged_even_with_name_label_nearby():
    raw = ("        Name: Audit (058264478258)\n"
           "        Conditions:\n"
           "          - Equals: 058264478258\n")
    diags = UnquotedAccountIdRule().check({}, _raw_ctx(raw))
    assert len(diags) == 1
    assert diags[0].line == 3


def test_block_list_item_unquoted_id_flagged():
    raw = ("        Equals:\n"
           "          - 058264478258\n")
    diags = UnquotedAccountIdRule().check({}, _raw_ctx(raw))
    assert len(diags) == 1


def test_flow_sequence_unquoted_ids_flagged():
    raw = "          - Equals: [123456789012, 234567890123]\n"
    diags = UnquotedAccountIdRule().check({}, _raw_ctx(raw))
    assert len(diags) == 2


def test_id_embedded_in_freeform_text_not_flagged():
    raw = "        Name: account 123456789012 prod\n"
    assert UnquotedAccountIdRule().check({}, _raw_ctx(raw)) == []


def test_quoted_value_still_not_flagged():
    raw = "          - Equals: '058264478258'\n"
    assert UnquotedAccountIdRule().check({}, _raw_ctx(raw)) == []
