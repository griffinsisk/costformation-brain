"""Integration tests for the telemetry_check.py CLI."""
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(REPO_ROOT, "validator", "telemetry_check.py")
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

VALID = os.path.join(FIXTURES, "telemetry_valid.json")
INVALID = os.path.join(FIXTURES, "telemetry_invalid.json")
TARGET = os.path.join(FIXTURES, "telemetry_target.yaml")


def run_check(*args):
    return subprocess.run([sys.executable, CHECK, *args],
                          capture_output=True, text=True)


def test_valid_payload_exits_0():
    result = run_check(VALID)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_invalid_payload_exits_1_and_reports_each_problem():
    result = run_check(INVALID)
    assert result.returncode == 1
    for rule_id in ("telemetry-timestamp-not-hourly", "telemetry-bad-granularity",
                    "telemetry-filter-cf-syntax", "telemetry-bad-value"):
        assert rule_id in result.stdout, rule_id


def test_element_cross_check_catches_case_mismatch():
    result = run_check(INVALID, "--costformation", TARGET,
                       "--target-dimension", "SpendCategory")
    assert result.returncode == 1
    assert "telemetry-unknown-element" in result.stdout


def test_valid_payload_with_cross_check_exits_0():
    result = run_check(VALID, "--costformation", TARGET,
                       "--target-dimension", "SpendCategory")
    assert result.returncode == 0, result.stdout + result.stderr


def test_groupby_target_skips_element_check_with_note():
    result = run_check(VALID, "--costformation", TARGET,
                       "--target-dimension", "DynamicTeams")
    assert result.returncode == 0
    assert "GroupBy" in result.stdout  # note explaining the skip


def test_json_format():
    result = run_check(INVALID, "--format", "json")
    data = json.loads(result.stdout)
    assert data["summary"]["errors"] >= 4


def test_no_args_exits_2():
    result = run_check()
    assert result.returncode == 2


def test_missing_dimension_exits_2():
    result = run_check(VALID, "--costformation", TARGET,
                       "--target-dimension", "Nope")
    assert result.returncode == 2
