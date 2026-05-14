#!/usr/bin/env python3
"""Eval runner CLI for CostFormation golden-output testing.

Usage:
    python3 evals/run.py --list
    python3 evals/run.py --validate-golden [--case <test_id>]
    python3 evals/run.py --assert-golden [--case <test_id>]
    python3 evals/run.py --validate-golden --assert-golden [--case <test_id>]

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
    2 — CLI usage error
"""
from __future__ import annotations

import argparse
import os
import sys
import pathlib
from typing import Dict, List, Optional, Any

# Add repo root to sys.path so `validator.*` and `evals.*` are importable.
_REPO_ROOT = str(pathlib.Path(__file__).parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from ruamel.yaml import YAML
from validator.lint import lint_file
from validator.diagnostic import Severity
from evals.assertions import check_assertions, AssertionResult

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases")
EVALS_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Case loading
# ---------------------------------------------------------------------------

def load_cases(case_filter: Optional[str] = None) -> List[Dict]:
    """Load all YAML case files from CASES_DIR, optionally filtered by test_id."""
    yaml = YAML()
    yaml.preserve_quotes = True

    cases = []
    for filename in sorted(os.listdir(CASES_DIR)):
        if not filename.endswith(".yaml"):
            continue
        filepath = os.path.join(CASES_DIR, filename)
        with open(filepath, "r") as fh:
            data = yaml.load(fh)
        if data is None:
            continue
        if case_filter is not None and data.get("test_id") != case_filter:
            continue
        cases.append(data)

    return cases


# ---------------------------------------------------------------------------
# Command: list
# ---------------------------------------------------------------------------

def cmd_list(args: argparse.Namespace) -> int:
    """Print each case: test_id, complexity, description."""
    cases = load_cases(args.case)
    for case in cases:
        test_id = str(case.get("test_id", "")).ljust(35)
        complexity = str(case.get("complexity", "")).ljust(14)
        description = str(case.get("description", ""))
        print(f"{test_id}{complexity}{description}")
    return 0


# ---------------------------------------------------------------------------
# Command: validate-golden
# ---------------------------------------------------------------------------

def cmd_validate_golden(args: argparse.Namespace) -> int:
    """Validate each golden output file against its expected_validator status."""
    cases = load_cases(args.case)
    total = len(cases)
    passed = 0

    for case in cases:
        test_id = case.get("test_id", "<unknown>")
        golden_rel = case.get("golden_output", "")
        golden_path = os.path.join(EVALS_DIR, golden_rel)

        expected = case.get("expected_validator", {}) or {}
        expected_status = expected.get("status", "pass")
        expected_rule_ids = expected.get("rule_ids") or []

        diagnostics = lint_file(golden_path, standalone=True)
        error_count = sum(1 for d in diagnostics if d.severity == Severity.ERROR)
        warn_count = sum(1 for d in diagnostics if d.severity == Severity.WARN)
        actual_rule_ids = {d.rule_id for d in diagnostics if d.severity == Severity.ERROR}

        ok = False
        if expected_status == "pass":
            ok = error_count == 0
        elif expected_status == "error":
            ok = error_count > 0 and all(r in actual_rule_ids for r in expected_rule_ids)
        elif expected_status == "warning":
            actual_warn_rule_ids = {d.rule_id for d in diagnostics if d.severity == Severity.WARN}
            ok = warn_count > 0 and all(r in actual_warn_rule_ids for r in expected_rule_ids)

        status_str = "PASS" if ok else "FAIL"
        print(f"{status_str}  {test_id}  (errors={error_count}, warnings={warn_count})")

        if not ok:
            for diag in diagnostics:
                print(f"      {diag.human_readable(golden_path)}")
        else:
            passed += 1

    print(f"\n{passed}/{total} passed")
    return 0 if passed == total else 1


# ---------------------------------------------------------------------------
# Command: assert-golden
# ---------------------------------------------------------------------------

def cmd_assert_golden(args: argparse.Namespace) -> int:
    """Run assertions against each golden output file."""
    cases = load_cases(args.case)
    total_cases = len(cases)
    cases_passed = 0
    total_assertions = 0
    total_failed = 0
    total_skipped = 0

    for case in cases:
        test_id = case.get("test_id", "<unknown>")
        golden_rel = case.get("golden_output", "")
        golden_path = os.path.join(EVALS_DIR, golden_rel)
        assertions: List[Dict] = case.get("assertions") or []

        diagnostics = lint_file(golden_path, standalone=True)
        results: List[AssertionResult] = check_assertions(assertions, golden_path, diagnostics)

        case_failed = sum(1 for r in results if not r.passed and not r.skipped)
        case_skipped = sum(1 for r in results if r.skipped)

        print(f"\n--- {test_id} ---")
        for result in results:
            if result.skipped:
                symbol = "?"
            elif result.passed:
                symbol = "✓"
            else:
                symbol = "✗"
            print(f"  {symbol} [{result.type}] {result.message}")

        total_assertions += len(results)
        total_failed += case_failed
        total_skipped += case_skipped

        if case_failed == 0:
            cases_passed += 1

    print(
        f"\n{cases_passed}/{total_cases} cases passed, "
        f"{total_assertions} assertions checked, "
        f"{total_failed} failed, "
        f"{total_skipped} skipped"
    )
    return 0 if total_failed == 0 else 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Eval runner for CostFormation golden-output testing.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--list", action="store_true", help="List all eval cases")
    parser.add_argument(
        "--validate-golden",
        action="store_true",
        help="Validate golden outputs against expected_validator status",
    )
    parser.add_argument(
        "--assert-golden",
        action="store_true",
        help="Run assertion checks against golden outputs",
    )
    parser.add_argument(
        "--case",
        metavar="TEST_ID",
        default=None,
        help="Filter to a single test case by test_id",
    )

    args = parser.parse_args()

    if not args.list and not args.validate_golden and not args.assert_golden:
        parser.print_help()
        sys.exit(2)

    if args.list:
        sys.exit(cmd_list(args))

    exit_code = 0

    if args.validate_golden:
        rc = cmd_validate_golden(args)
        exit_code = max(exit_code, rc)

    if args.assert_golden:
        rc = cmd_assert_golden(args)
        exit_code = max(exit_code, rc)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
