"""Tests for performance rules."""
import os
import textwrap
import tempfile

import pytest

from validator.parser import parse_costformation
from validator.diagnostic import Severity
from validator.rules.performance import (
    DefaultValueAllocationInputRule,
    AllocateByStreamsSPTARule,
    LayeredAllocationRule,
    DefaultValueNoIntentRule,
    BroadSpendToAllocateRule,
    RegexUnnecessaryRule,
    VisibleNoChildRule,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
VALID_ALLOCATION = os.path.join(FIXTURES_DIR, "valid_allocation.yaml")
INVALID_DEFAULTVALUE = os.path.join(FIXTURES_DIR, "invalid_defaultvalue.yaml")


def _parse(filepath):
    result = parse_costformation(filepath)
    context = {
        "filename": result.filename,
        "standalone": result.standalone,
        "raw_text": result.raw_text,
        "yaml_obj": result.yaml_obj,
    }
    return result.dimensions, context


def _parse_inline(yaml_text: str):
    """Write yaml_text to a temp file, parse it, and return (dimensions, context)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(textwrap.dedent(yaml_text))
        f.flush()
        path = f.name
    try:
        return _parse(path)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# DefaultValueAllocationInputRule
# ---------------------------------------------------------------------------

class TestDefaultValueAllocationInput:

    def test_catches_defaultvalue_on_hidden_dim(self):
        dims, ctx = _parse(INVALID_DEFAULTVALUE)
        diags = DefaultValueAllocationInputRule().check(dims, ctx)
        matched = [d for d in diags if d.dimension_id == "SharedSpend"]
        assert len(matched) == 1
        assert matched[0].severity == Severity.ERROR
        assert matched[0].rule_id == "defaultvalue-allocation-input"

    def test_passes_valid_allocation(self):
        dims, ctx = _parse(VALID_ALLOCATION)
        diags = DefaultValueAllocationInputRule().check(dims, ctx)
        assert diags == []

    def test_ignores_allocation_type_with_defaultvalue(self):
        """An Allocation dim itself is allowed to have DefaultValue + Hide."""
        dims, ctx = _parse_inline("""\
            Dimensions:
              AllocDim:
                Name: Alloc Dim
                Type: Allocation
                Hide: true
                DefaultValue: Unallocated
                AllocateByRules:
                  SpendToAllocate:
                    Conditions:
                      - Source: Tag:pool
                        Equals: shared
        """)
        diags = DefaultValueAllocationInputRule().check(dims, ctx)
        assert diags == []


# ---------------------------------------------------------------------------
# AllocateByStreamsSPTARule
# ---------------------------------------------------------------------------

class TestAllocateByStreamsSPTA:

    def test_catches_spendtoallocate_under_streams(self):
        dims, ctx = _parse(INVALID_DEFAULTVALUE)
        diags = AllocateByStreamsSPTARule().check(dims, ctx)
        matched = [d for d in diags if d.dimension_id == "SharedAllocation"]
        assert len(matched) == 1
        assert matched[0].severity == Severity.ERROR
        assert matched[0].rule_id == "allocatebystreams-spendtoallocate"

    def test_passes_valid_streams(self):
        dims, ctx = _parse(VALID_ALLOCATION)
        diags = AllocateByStreamsSPTARule().check(dims, ctx)
        assert diags == []


# ---------------------------------------------------------------------------
# LayeredAllocationRule
# ---------------------------------------------------------------------------

class TestLayeredAllocation:

    def test_catches_allocation_referencing_allocation(self):
        dims, ctx = _parse_inline("""\
            Dimensions:
              BaseAlloc:
                Name: Base Allocation
                Type: Allocation
                Hide: true
                AllocateByRules:
                  SpendToAllocate:
                    Conditions:
                      - Source: Tag:pool
                        Equals: shared

              LayeredAlloc:
                Name: Layered Allocation
                Type: Allocation
                Hide: true
                AllocateByRules:
                  SpendToAllocate:
                    Conditions:
                      - Source: User:Defined:BaseAlloc
                        Equals: shared
        """)
        diags = LayeredAllocationRule().check(dims, ctx)
        assert len(diags) == 1
        assert diags[0].severity == Severity.ERROR
        assert diags[0].rule_id == "layered-allocation"
        assert diags[0].dimension_id == "LayeredAlloc"

    def test_passes_allocation_referencing_non_allocation(self):
        dims, ctx = _parse_inline("""\
            Dimensions:
              Helper:
                Name: Helper
                Hide: true
                Rules:
                  - Type: Group
                    Name: Pool
                    Conditions:
                      - Source: Tag:pool
                        Equals: shared

              AllocDim:
                Name: Alloc Dim
                Type: Allocation
                Hide: true
                AllocateByRules:
                  SpendToAllocate:
                    Conditions:
                      - Source: User:Defined:Helper
                        Equals: Pool
        """)
        diags = LayeredAllocationRule().check(dims, ctx)
        assert diags == []


# ---------------------------------------------------------------------------
# DefaultValueNoIntentRule
# ---------------------------------------------------------------------------

class TestDefaultValueNoIntent:

    def test_warns_when_no_comment(self):
        dims, ctx = _parse(INVALID_DEFAULTVALUE)
        diags = DefaultValueNoIntentRule().check(dims, ctx)
        matched = [d for d in diags if d.dimension_id == "SharedSpend"]
        assert len(matched) == 1
        assert matched[0].severity == Severity.WARN
        assert matched[0].rule_id == "defaultvalue-no-intent"

    def test_passes_when_comment_present(self):
        dims, ctx = _parse_inline("""\
            Dimensions:
              Env:
                Name: Environment
                DefaultValue: Unknown  # intentional catch-all for untagged
                Rules:
                  - Type: Group
                    Name: Production
                    Conditions:
                      - Source: Tag:env
                        Equals: prod
        """)
        diags = DefaultValueNoIntentRule().check(dims, ctx)
        assert diags == []


# ---------------------------------------------------------------------------
# BroadSpendToAllocateRule
# ---------------------------------------------------------------------------

class TestBroadSpendToAllocate:

    def test_warns_single_condition_no_and(self):
        dims, ctx = _parse_inline("""\
            Dimensions:
              AllocDim:
                Name: Alloc Dim
                Type: Allocation
                AllocateByRules:
                  SpendToAllocate:
                    Conditions:
                      - Source: Tag:pool
                        Equals: shared
        """)
        diags = BroadSpendToAllocateRule().check(dims, ctx)
        assert len(diags) == 1
        assert diags[0].severity == Severity.WARN
        assert diags[0].rule_id == "broad-spendtoallocate"

    def test_passes_with_and_wrapper(self):
        dims, ctx = _parse_inline("""\
            Dimensions:
              AllocDim:
                Name: Alloc Dim
                Type: Allocation
                AllocateByRules:
                  SpendToAllocate:
                    Conditions:
                      - And:
                          - Source: Tag:pool
                            Equals: shared
                          - Source: Account
                            Equals: '123456789012'
        """)
        diags = BroadSpendToAllocateRule().check(dims, ctx)
        assert diags == []


# ---------------------------------------------------------------------------
# RegexUnnecessaryRule
# ---------------------------------------------------------------------------

class TestRegexUnnecessary:

    def test_warns_on_simple_pattern(self):
        dims, ctx = _parse_inline("""\
            Dimensions:
              Env:
                Name: Environment
                Rules:
                  - Type: Group
                    Name: Prod
                    Conditions:
                      - Source: Tag:env
                        Matches: ^production$
        """)
        diags = RegexUnnecessaryRule().check(dims, ctx)
        assert len(diags) == 1
        assert diags[0].severity == Severity.WARN
        assert diags[0].rule_id == "regex-unnecessary"

    def test_passes_real_regex(self):
        dims, ctx = _parse_inline("""\
            Dimensions:
              Env:
                Name: Environment
                Rules:
                  - Type: Group
                    Name: Prod
                    Conditions:
                      - Source: Tag:env
                        Matches: ^prod(uction)?$
        """)
        diags = RegexUnnecessaryRule().check(dims, ctx)
        assert diags == []


# ---------------------------------------------------------------------------
# VisibleNoChildRule
# ---------------------------------------------------------------------------

class TestVisibleNoChild:

    def test_visible_no_child_skips_hidden(self):
        dims, ctx = _parse(VALID_ALLOCATION)
        diags = VisibleNoChildRule().check(dims, ctx)
        # SpendCategory is hidden, SharedAllocation is Allocation type
        # TeamCosts has Child — so no warnings expected
        assert diags == []

    def test_visible_no_child_warns_on_visible(self):
        dims, ctx = _parse_inline("""\
            Dimensions:
              Env:
                Name: Environment
                Rules:
                  - Type: Group
                    Name: Prod
                    Conditions:
                      - Source: Tag:env
                        Equals: prod
        """)
        diags = VisibleNoChildRule().check(dims, ctx)
        assert len(diags) == 1
        assert diags[0].severity == Severity.WARN
        assert diags[0].rule_id == "visible-no-child"
        assert diags[0].dimension_id == "Env"

    def test_visible_no_child_skips_disabled(self):
        dims, ctx = _parse_inline("""\
            Dimensions:
              Env:
                Name: Environment
                Disable: true
                Rules:
                  - Type: Group
                    Name: Prod
                    Conditions:
                      - Source: Tag:env
                        Equals: prod
        """)
        diags = VisibleNoChildRule().check(dims, ctx)
        assert diags == []
