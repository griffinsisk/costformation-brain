"""Integrity rule for my-org/onboarding-state.yaml (the onboarding journey).

The state file is the deterministic backstop against agent drift: completed
phases must carry recorded exit-check results, waiting-external entries must
carry verify-after dates. A loosely-following agent leaves a state file that
fails these checks.

Schema is defined in onboarding/journey.md; the constants below mirror it.
"""
import pathlib
from typing import List

from ruamel.yaml import YAML, YAMLError

from validator.diagnostic import Diagnostic, Severity
from validator.rules import Rule

VALID_PHASES = ["discover", "dimensions", "shared-spend", "allocation", "unit-cost"]
VALID_STATUSES = {"not_started", "in_progress", "complete", "skipped",
                  "waiting-external"}

STATE_RELPATH = pathlib.Path("my-org") / "onboarding-state.yaml"


class OnboardingStateRule(Rule):
    """Validate onboarding-state.yaml structure and recorded transitions."""

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        return []

    def check_integrity(self, examples_dir: pathlib.Path) -> List[Diagnostic]:
        repo_root = pathlib.Path(examples_dir).parent
        state_path = repo_root / STATE_RELPATH
        if not state_path.exists():
            return []  # journey not started — nothing to validate

        relname = str(STATE_RELPATH)
        try:
            data = YAML().load(state_path.read_text())
        except (YAMLError, OSError) as exc:
            return [Diagnostic(severity=Severity.ERROR,
                               rule_id="onboarding-parse-error",
                               message=f"cannot parse {relname}: {exc}",
                               path=relname)]
        if not isinstance(data, dict):
            return [Diagnostic(severity=Severity.ERROR,
                               rule_id="onboarding-parse-error",
                               message=f"{relname} must be a YAML mapping",
                               path=relname)]

        diagnostics: List[Diagnostic] = []
        phases = data.get("phases") or {}
        if not isinstance(phases, dict):
            diagnostics.append(Diagnostic(
                severity=Severity.ERROR, rule_id="onboarding-parse-error",
                message=f"{relname}: 'phases' must be a mapping of phase name "
                        f"to entry, got {type(phases).__name__}", path=relname))
            phases = {}

        for phase_name, entry in phases.items():
            if phase_name not in VALID_PHASES:
                diagnostics.append(Diagnostic(
                    severity=Severity.ERROR, rule_id="onboarding-unknown-phase",
                    message=f"unknown phase '{phase_name}' "
                            f"(valid: {VALID_PHASES})", path=relname))
                continue
            if isinstance(entry, dict):
                diagnostics.extend(self._check_entry(
                    entry, f"phases.{phase_name}", repo_root, relname))
                per_dim = entry.get("per-dimension") or {}
                if isinstance(per_dim, dict):
                    for dim_name, dim_entry in per_dim.items():
                        if isinstance(dim_entry, dict):
                            diagnostics.extend(self._check_entry(
                                dim_entry,
                                f"phases.{phase_name}.per-dimension.{dim_name}",
                                repo_root, relname))
        return diagnostics

    def _check_entry(self, entry: dict, where: str, repo_root: pathlib.Path,
                     relname: str) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        status = entry.get("status")

        if status is not None and status not in VALID_STATUSES:
            diagnostics.append(Diagnostic(
                severity=Severity.ERROR, rule_id="onboarding-bad-status",
                message=f"{where}: status '{status}' is not one of "
                        f"{sorted(VALID_STATUSES)}", path=relname))

        if status == "complete" and not entry.get("exit-checks"):
            diagnostics.append(Diagnostic(
                severity=Severity.ERROR, rule_id="onboarding-missing-exit-checks",
                message=f"{where}: status is 'complete' but no exit-checks "
                        f"are recorded — phase transitions must record their "
                        f"verification results (journey.md)", path=relname))

        if status == "waiting-external" and not entry.get("verify-after"):
            diagnostics.append(Diagnostic(
                severity=Severity.ERROR, rule_id="onboarding-missing-verify-after",
                message=f"{where}: status is 'waiting-external' but no "
                        f"verify-after date is set — the session-start wait "
                        f"check needs it to surface overdue work", path=relname))

        for artifact in entry.get("artifacts") or []:
            if isinstance(artifact, str) and not (repo_root / artifact).exists():
                diagnostics.append(Diagnostic(
                    severity=Severity.WARN, rule_id="onboarding-missing-artifact",
                    message=f"{where}: recorded artifact '{artifact}' not "
                            f"found on disk", path=relname))
        return diagnostics
