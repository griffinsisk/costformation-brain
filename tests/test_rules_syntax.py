"""Tests for syntax rules: missing-type and unquoted-account-id."""
import os

import pytest

from validator.parser import parse_costformation
from validator.diagnostic import Severity
from validator.rules.syntax import MissingTypeRule, UnquotedAccountIdRule

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VALID_BASIC = os.path.join(FIXTURES_DIR, "valid_basic.yaml")
INVALID_TYPE = os.path.join(FIXTURES_DIR, "invalid_type.yaml")
INVALID_ACCOUNT_IDS = os.path.join(FIXTURES_DIR, "invalid_account_ids.yaml")


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
