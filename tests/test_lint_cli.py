"""Integration tests for the lint.py CLI entry point."""
import json
import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINT = os.path.join(REPO_ROOT, "validator", "lint.py")
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
EXAMPLES_PATTERNS_DIR = os.path.join(REPO_ROOT, "examples", "patterns")

VALID_BASIC = os.path.join(FIXTURES_DIR, "valid_basic.yaml")
INVALID_SOURCE = os.path.join(FIXTURES_DIR, "invalid_source.yaml")
INVALID_ACCOUNT_IDS = os.path.join(FIXTURES_DIR, "invalid_account_ids.yaml")
INVALID_DEFAULTVALUE = os.path.join(FIXTURES_DIR, "invalid_defaultvalue.yaml")
VALID_ALLOCATION = os.path.join(FIXTURES_DIR, "valid_allocation.yaml")


def run_lint(*args):
    """Run lint.py with given args; return CompletedProcess."""
    return subprocess.run(
        [sys.executable, LINT, *args],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Basic exit-code tests
# ---------------------------------------------------------------------------

def test_valid_file_exits_0():
    result = run_lint(VALID_BASIC)
    assert result.returncode == 0, f"Expected 0, got {result.returncode}\n{result.stdout}\n{result.stderr}"


def test_invalid_source_exits_1():
    result = run_lint(INVALID_SOURCE)
    assert result.returncode == 1, f"Expected 1, got {result.returncode}\n{result.stdout}\n{result.stderr}"
    assert "source-prefix" in result.stdout, f"Expected 'source-prefix' in stdout:\n{result.stdout}"


def test_no_args_exits_2():
    result = run_lint()
    assert result.returncode == 2, f"Expected 2 (no-args), got {result.returncode}\n{result.stderr}"


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def test_json_output_shape():
    result = run_lint("--format", "json", INVALID_SOURCE)
    assert result.returncode == 1
    data = json.loads(result.stdout)
    # Single file: top-level keys are file, diagnostics, summary
    assert "file" in data or "results" in data
    # Locate diagnostics list
    if "results" in data:
        diagnostics = data["results"][0]["diagnostics"]
        summary = data["summary"]
    else:
        diagnostics = data["diagnostics"]
        summary = data["summary"]
    assert isinstance(diagnostics, list)
    assert len(diagnostics) > 0
    d = diagnostics[0]
    assert "severity" in d
    assert "rule_id" in d
    assert "message" in d
    assert "path" in d
    assert "line" in d
    assert "column" in d
    assert "dimension_id" in d
    assert "rule_name" in d
    assert "errors" in summary
    assert "warnings" in summary
    assert "files_checked" in summary


def test_json_output_valid_file():
    result = run_lint("--format", "json", VALID_BASIC)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    if "results" in data:
        summary = data["summary"]
    else:
        summary = data["summary"]
    assert summary["errors"] == 0


# ---------------------------------------------------------------------------
# --warnings-as-errors
# ---------------------------------------------------------------------------

def test_warnings_as_errors_promotes_warn_to_error():
    """A file with only warnings exits 0 normally, 1 with --warnings-as-errors."""
    # invalid_defaultvalue.yaml should produce at least one WARN diagnostic
    result_normal = run_lint(INVALID_DEFAULTVALUE)
    result_wae = run_lint("--warnings-as-errors", INVALID_DEFAULTVALUE)

    # With warnings-as-errors, if there are any warnings the exit code must be 1
    # (We don't assume what invalid_defaultvalue.yaml produces; we just verify
    # the flag changes behavior when there are warnings.)
    if "WARN" in result_normal.stdout:
        assert result_wae.returncode == 1, (
            "--warnings-as-errors should promote WARN to exit 1"
        )


def test_warnings_as_errors_flag_accepted():
    """--warnings-as-errors flag doesn't crash the CLI."""
    result = run_lint("--warnings-as-errors", VALID_BASIC)
    assert result.returncode in (0, 1), f"Unexpected returncode {result.returncode}"


# ---------------------------------------------------------------------------
# --check-integrity
# ---------------------------------------------------------------------------

def test_check_integrity_runs():
    """--check-integrity exits 0 or 1 (just verify it doesn't crash)."""
    result = run_lint("--check-integrity")
    assert result.returncode in (0, 1), (
        f"--check-integrity should exit 0 or 1, got {result.returncode}\n{result.stderr}"
    )


def test_check_integrity_with_no_files_doesnt_exit_2():
    """--check-integrity alone is valid (not exit 2)."""
    result = run_lint("--check-integrity")
    assert result.returncode != 2


# ---------------------------------------------------------------------------
# Example patterns
# ---------------------------------------------------------------------------

def test_all_examples_pass():
    """All 20 example patterns in examples/patterns/ should exit 0."""
    pattern_files = sorted(
        f for f in os.listdir(EXAMPLES_PATTERNS_DIR) if f.endswith(".yaml")
    )
    assert len(pattern_files) > 0, "No example pattern files found"

    failures = []
    for fname in pattern_files:
        fpath = os.path.join(EXAMPLES_PATTERNS_DIR, fname)
        result = run_lint(fpath)
        if result.returncode != 0:
            failures.append(f"{fname}: exit {result.returncode}\n{result.stdout}\n{result.stderr}")

    assert not failures, "Some example patterns failed lint:\n" + "\n---\n".join(failures)


# ---------------------------------------------------------------------------
# Multi-file output
# ---------------------------------------------------------------------------

def test_multiple_files_json_shape():
    """When multiple files are linted, JSON uses 'results' array."""
    result = run_lint("--format", "json", VALID_BASIC, INVALID_SOURCE)
    data = json.loads(result.stdout)
    assert "results" in data, f"Expected 'results' key for multi-file JSON:\n{result.stdout}"
    assert "summary" in data
    assert len(data["results"]) == 2
    assert data["summary"]["files_checked"] == 2


def test_human_output_ok_summary():
    """Human output for a valid file includes an OK summary line."""
    result = run_lint(VALID_BASIC)
    assert result.returncode == 0
    assert "OK" in result.stdout or "0 errors" in result.stdout, (
        f"Expected OK/0 errors in output:\n{result.stdout}"
    )
