"""Tests for integrity rules: index consistency, metadata completeness, customer data leak."""
import pathlib
import pytest

from validator.rules.integrity import (
    IndexConsistencyRule,
    MetadataIncompleteRule,
    CustomerDataLeakRule,
)
from validator.diagnostic import Severity

EXAMPLES_DIR = pathlib.Path(__file__).parent.parent / "examples"


def test_all_indexed_files_exist():
    """Every file: path listed in index.yaml must exist on disk."""
    rule = IndexConsistencyRule()
    diagnostics = rule.check_integrity(EXAMPLES_DIR)
    missing = [d for d in diagnostics if d.rule_id == "index-missing-file"]
    assert missing == [], (
        f"Index entries point to non-existent files:\n"
        + "\n".join(f"  {d.message}" for d in missing)
    )


def test_all_pattern_files_indexed():
    """Every *.yaml in examples/patterns/ must have an entry in index.yaml."""
    rule = IndexConsistencyRule()
    diagnostics = rule.check_integrity(EXAMPLES_DIR)
    unindexed = [d for d in diagnostics if d.rule_id == "index-unindexed-pattern"]
    assert unindexed == [], (
        f"Pattern files not listed in index.yaml:\n"
        + "\n".join(f"  {d.message}" for d in unindexed)
    )


def test_all_index_entries_have_required_fields():
    """Every index entry must include all 8 required metadata fields."""
    rule = MetadataIncompleteRule()
    diagnostics = rule.check_integrity(EXAMPLES_DIR)
    assert diagnostics == [], (
        f"Index entries missing required metadata fields:\n"
        + "\n".join(f"  {d.message}" for d in diagnostics)
    )


def test_no_customer_names_in_examples():
    """No example pattern files should contain blocked customer names or reference/ paths."""
    rule = CustomerDataLeakRule()
    diagnostics = rule.check_integrity(EXAMPLES_DIR)
    errors = [d for d in diagnostics if d.severity == Severity.ERROR]
    assert errors == [], (
        f"Potential customer data found in examples/:\n"
        + "\n".join(f"  {d.message}" for d in errors)
    )
