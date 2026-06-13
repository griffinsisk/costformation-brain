"""Tests for the onboarding-state integrity rule.

check_integrity(examples_dir) derives the repo root as examples_dir.parent
and looks for my-org/onboarding-state.yaml there, so tests build a fake repo
in tmp_path: tmp_path/examples/ + tmp_path/my-org/onboarding-state.yaml.
"""
import pathlib
import textwrap

import pytest

from validator.rules.onboarding_state import OnboardingStateRule
from validator.diagnostic import Severity


def make_repo(tmp_path, state_yaml=None):
    (tmp_path / "examples").mkdir()
    if state_yaml is not None:
        (tmp_path / "my-org").mkdir()
        (tmp_path / "my-org" / "onboarding-state.yaml").write_text(
            textwrap.dedent(state_yaml))
    return tmp_path / "examples"


VALID_STATE = """\
    journey:
      offered: 2026-06-12
      declined: false
      current-phase: 4
    phases:
      discover:
        status: complete
        exit-checks:
          - check: signal inventory presented and confirmed
            result: pass
            date: 2026-06-12
      dimensions:
        status: complete
        exit-checks:
          - check: validator passes on starter set
            result: pass
            date: 2026-06-12
      shared-spend:
        status: in_progress
      allocation:
        status: in_progress
        per-dimension:
          Team:
            status: skipped
            reason: fully covered by tags
          Customer:
            status: waiting-external
            stream: tenant-usage
            verify-after: 2026-06-14
      unit-cost:
        status: not_started
"""


def _ids(diags):
    return [d.rule_id for d in diags]


def test_missing_state_file_is_silent(tmp_path):
    examples = make_repo(tmp_path, state_yaml=None)
    assert OnboardingStateRule().check_integrity(examples) == []


def test_valid_state_file_passes(tmp_path):
    examples = make_repo(tmp_path, VALID_STATE)
    assert OnboardingStateRule().check_integrity(examples) == []


def test_unknown_phase_is_error(tmp_path):
    examples = make_repo(tmp_path, VALID_STATE.replace("unit-cost:", "unitcost:"))
    diags = OnboardingStateRule().check_integrity(examples)
    assert "onboarding-unknown-phase" in _ids(diags)


def test_bad_status_is_error(tmp_path):
    examples = make_repo(tmp_path, VALID_STATE.replace(
        "status: not_started", "status: pending"))
    diags = OnboardingStateRule().check_integrity(examples)
    assert "onboarding-bad-status" in _ids(diags)


def test_complete_without_exit_checks_is_error(tmp_path):
    bad = VALID_STATE.replace(
        """\
      shared-spend:
        status: in_progress
""",
        """\
      shared-spend:
        status: complete
""")
    examples = make_repo(tmp_path, bad)
    diags = OnboardingStateRule().check_integrity(examples)
    assert "onboarding-missing-exit-checks" in _ids(diags)


def test_waiting_external_without_verify_after_is_error(tmp_path):
    bad = VALID_STATE.replace("            verify-after: 2026-06-14\n", "")
    examples = make_repo(tmp_path, bad)
    diags = OnboardingStateRule().check_integrity(examples)
    assert "onboarding-missing-verify-after" in _ids(diags)


def test_missing_artifact_is_warning(tmp_path):
    bad = VALID_STATE.replace(
        "        exit-checks:\n"
        "          - check: validator passes on starter set\n"
        "            result: pass\n"
        "            date: 2026-06-12\n",
        "        exit-checks:\n"
        "          - check: validator passes on starter set\n"
        "            result: pass\n"
        "            date: 2026-06-12\n"
        "        artifacts:\n"
        "          - team-dimension_2026-06-12/\n")
    examples = make_repo(tmp_path, bad)
    diags = OnboardingStateRule().check_integrity(examples)
    art = [d for d in diags if d.rule_id == "onboarding-missing-artifact"]
    assert len(art) == 1
    assert art[0].severity == Severity.WARN


def test_unparseable_state_file_is_error(tmp_path):
    examples = make_repo(tmp_path, "phases: [unclosed")
    diags = OnboardingStateRule().check_integrity(examples)
    assert "onboarding-parse-error" in _ids(diags)
