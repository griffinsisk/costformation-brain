#!/usr/bin/env python3
"""CLI entry point for the CostFormation YAML validator.

Usage:
    python3 validator/lint.py [--format human|json] [--warnings-as-errors]
                              [--check-integrity] [--standalone] [files...]

Exit codes:
    0 — no errors (warnings may be present)
    1 — one or more errors found
    2 — CLI usage error (no files and no --check-integrity)
"""
import argparse
import json
import os
import pathlib
import sys
from typing import List, Optional

# Ensure the repo root (parent of validator/) is on sys.path so that
# `validator.*` imports work when the script is run directly.
_REPO_ROOT = str(pathlib.Path(__file__).parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from validator.diagnostic import Diagnostic, Severity
from validator.parser import ParseError, parse_costformation
from validator.rules.integrity import (
    CustomerDataLeakRule,
    IndexConsistencyRule,
    MetadataIncompleteRule,
)
from validator.rules.performance import (
    AllocateByStreamsSPTARule,
    BroadSpendToAllocateRule,
    DefaultValueAllocationInputRule,
    DefaultValueNoIntentRule,
    LayeredAllocationRule,
    RegexUnnecessaryRule,
    VisibleNoChildRule,
)
from validator.rules.sources import SourcePrefixRule, UnresolvedUserDefinedRule
from validator.rules.syntax import MissingTypeRule, UnquotedAccountIdRule

# All non-integrity rules run on every file.
ALL_RULES = [
    MissingTypeRule(),
    UnquotedAccountIdRule(),
    SourcePrefixRule(),
    UnresolvedUserDefinedRule(),
    DefaultValueAllocationInputRule(),
    DefaultValueNoIntentRule(),
    AllocateByStreamsSPTARule(),
    LayeredAllocationRule(),
    BroadSpendToAllocateRule(),
    RegexUnnecessaryRule(),
    VisibleNoChildRule(),
]

# Integrity rules operate on the examples directory, not individual files.
INTEGRITY_RULES = [
    IndexConsistencyRule(),
    MetadataIncompleteRule(),
    CustomerDataLeakRule(),
]


def lint_file(filepath: str, standalone: Optional[bool] = None) -> List[Diagnostic]:
    """Parse *filepath* and run all non-integrity rules.

    On ParseError, returns a single ERROR diagnostic with rule_id 'yaml-parse-error'.
    """
    try:
        result = parse_costformation(filepath, standalone=standalone)
    except ParseError as exc:
        return [
            Diagnostic(
                severity=Severity.ERROR,
                rule_id="yaml-parse-error",
                message=str(exc),
                path=filepath,
            )
        ]

    context = {
        "filename": result.filename,
        "standalone": result.standalone,
        "raw_text": result.raw_text,
        "yaml_obj": result.yaml_obj,
    }

    diagnostics: List[Diagnostic] = []
    for rule in ALL_RULES:
        diagnostics.extend(rule.check(result.dimensions, context))
    return diagnostics


def run_integrity_checks(examples_dir: pathlib.Path) -> List[Diagnostic]:
    """Run all integrity rules against *examples_dir*."""
    diagnostics: List[Diagnostic] = []
    for rule in INTEGRITY_RULES:
        diagnostics.extend(rule.check_integrity(examples_dir))
    return diagnostics


def _has_errors(diagnostics: List[Diagnostic], warnings_as_errors: bool) -> bool:
    """Return True if *diagnostics* contains any error-level issues."""
    for d in diagnostics:
        if d.severity == Severity.ERROR:
            return True
        if warnings_as_errors and d.severity == Severity.WARN:
            return True
    return False


def _count_errors(diagnostics: List[Diagnostic], warnings_as_errors: bool) -> int:
    count = 0
    for d in diagnostics:
        if d.severity == Severity.ERROR:
            count += 1
        elif warnings_as_errors and d.severity == Severity.WARN:
            count += 1
    return count


def _count_warnings(diagnostics: List[Diagnostic], warnings_as_errors: bool) -> int:
    if warnings_as_errors:
        return 0
    return sum(1 for d in diagnostics if d.severity == Severity.WARN)


def format_human(
    all_diagnostics: List[Diagnostic],
    filename: str,
    warnings_as_errors: bool,
) -> str:
    """Return human-readable output for a single file's diagnostics."""
    lines = []
    for d in all_diagnostics:
        lines.append(d.human_readable(filename))
    return "\n".join(lines)


def format_json(
    file_results: List[tuple],
    warnings_as_errors: bool,
) -> str:
    """Return JSON output.

    *file_results* is a list of (filename, diagnostics) tuples.
    Single-file: ``{"file": ..., "diagnostics": [...], "summary": {...}}``.
    Multi-file: ``{"results": [...], "summary": {...}}``.
    """
    total_errors = 0
    total_warnings = 0

    def _diag_list(diagnostics):
        nonlocal total_errors, total_warnings
        result = []
        for d in diagnostics:
            total_errors += _count_errors([d], warnings_as_errors)
            total_warnings += _count_warnings([d], warnings_as_errors)
            result.append(d.to_dict())
        return result

    if len(file_results) == 1:
        filename, diagnostics = file_results[0]
        diag_list = _diag_list(diagnostics)
        summary = {
            "errors": total_errors,
            "warnings": total_warnings,
            "files_checked": 1,
        }
        return json.dumps({"file": filename, "diagnostics": diag_list, "summary": summary}, indent=2)
    else:
        results = []
        for filename, diagnostics in file_results:
            diag_list = _diag_list(diagnostics)
            results.append({"file": filename, "diagnostics": diag_list})
        summary = {
            "errors": total_errors,
            "warnings": total_warnings,
            "files_checked": len(file_results),
        }
        return json.dumps({"results": results, "summary": summary}, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lint CostFormation YAML files.",
        prog="lint.py",
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="One or more CostFormation YAML files to lint.",
    )
    parser.add_argument(
        "--format",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human).",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        default=False,
        help="Treat warnings as errors for the exit code.",
    )
    parser.add_argument(
        "--check-integrity",
        action="store_true",
        default=False,
        help="Run integrity checks on the examples/ directory.",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        default=False,
        help="Suppress unresolved-user-defined errors (standalone pattern mode).",
    )

    args = parser.parse_args()

    # Require at least one file OR --check-integrity
    if not args.files and not args.check_integrity:
        parser.print_usage(sys.stderr)
        sys.stderr.write("error: provide at least one FILE or use --check-integrity\n")
        sys.exit(2)

    # Auto-detect examples/ directory relative to this file
    this_dir = pathlib.Path(__file__).parent  # validator/
    examples_dir = this_dir.parent / "examples"

    all_diagnostics: List[Diagnostic] = []
    file_results: List[tuple] = []
    found_errors = False

    # --- Lint individual files ---
    standalone_flag = True if args.standalone else None

    for filepath in args.files:
        diagnostics = lint_file(filepath, standalone=standalone_flag)
        file_results.append((filepath, diagnostics))
        all_diagnostics.extend(diagnostics)
        if _has_errors(diagnostics, args.warnings_as_errors):
            found_errors = True

    # --- Integrity checks ---
    if args.check_integrity:
        integrity_diagnostics = run_integrity_checks(examples_dir)
        # Treat integrity results as a virtual "integrity" file
        file_results.append(("integrity", integrity_diagnostics))
        all_diagnostics.extend(integrity_diagnostics)
        if _has_errors(integrity_diagnostics, args.warnings_as_errors):
            found_errors = True

    # --- Output ---
    if args.format == "json":
        print(format_json(file_results, args.warnings_as_errors))
    else:
        # Human format
        output_lines = []
        for filepath, diagnostics in file_results:
            for d in diagnostics:
                output_lines.append(d.human_readable(filepath))

        total_errors = _count_errors(all_diagnostics, args.warnings_as_errors)
        total_warnings = _count_warnings(all_diagnostics, args.warnings_as_errors)
        files_checked = len(args.files) + (1 if args.check_integrity else 0)

        if output_lines:
            print("\n".join(output_lines))

        if total_errors == 0:
            print(f"OK: {files_checked} file{'s' if files_checked != 1 else ''}, "
                  f"0 errors, {total_warnings} warning{'s' if total_warnings != 1 else ''}")
        else:
            print(f"FAIL: {files_checked} file{'s' if files_checked != 1 else ''}, "
                  f"{total_errors} error{'s' if total_errors != 1 else ''}, "
                  f"{total_warnings} warning{'s' if total_warnings != 1 else ''}")

    sys.exit(1 if found_errors else 0)


if __name__ == "__main__":
    main()
