#!/usr/bin/env python3
"""Validate a two-file CostFormation build workspace."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import List

from ruamel.yaml import YAML, YAMLError

REPO_ROOT = str(Path(__file__).resolve().parents[1])
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from validator.diagnostic import Diagnostic, Severity
from validator.lint import lint_file
from validator.rules.onboarding_state import OnboardingStateRule


BASELINE_NAME = "costformation.cz.yaml"
PROPOSAL_NAME = "costformation.proposed.cz.yaml"
STATE_RELPATH = Path(".costformation") / "gathering-state.yaml"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _error(rule_id: str, message: str, path: Path) -> Diagnostic:
    return Diagnostic(Severity.ERROR, rule_id, message, str(path))


def record_baseline(workspace: Path) -> str:
    workspace = workspace.resolve()
    baseline = workspace / BASELINE_NAME
    state_path = workspace / STATE_RELPATH
    if not baseline.exists():
        raise FileNotFoundError(baseline)
    yaml = YAML()
    state = yaml.load(state_path.read_text())
    if not isinstance(state, dict) or not isinstance(
        state.get("workspace"), dict
    ):
        raise ValueError("workspace state must be a mapping")
    digest = sha256_file(baseline)
    state["workspace"]["baseline-sha256"] = digest
    with state_path.open("w") as handle:
        yaml.dump(state, handle)
    return digest


def check_workspace(workspace: Path) -> List[Diagnostic]:
    workspace = workspace.resolve()
    baseline = workspace / BASELINE_NAME
    proposal = workspace / PROPOSAL_NAME
    state_path = workspace / STATE_RELPATH
    diagnostics: List[Diagnostic] = []

    if not baseline.exists():
        return [
            _error(
                "workspace-baseline-missing",
                f"missing {BASELINE_NAME}",
                baseline,
            )
        ]
    if not proposal.exists():
        diagnostics.append(
            _error(
                "workspace-proposal-missing",
                f"missing {PROPOSAL_NAME}",
                proposal,
            )
        )
    if not state_path.exists():
        diagnostics.append(
            _error(
                "workspace-state-missing",
                f"missing {STATE_RELPATH}",
                state_path,
            )
        )
        return diagnostics

    try:
        state = YAML().load(state_path.read_text())
    except (YAMLError, OSError) as exc:
        diagnostics.append(
            _error("workspace-state-invalid", str(exc), state_path)
        )
        return diagnostics

    workspace_state = state.get("workspace") if isinstance(state, dict) else None
    if not isinstance(workspace_state, dict):
        diagnostics.append(
            _error(
                "workspace-state-invalid",
                "workspace state must be a mapping",
                state_path,
            )
        )
        return diagnostics

    recorded_hash = workspace_state.get("baseline-sha256")
    current_hash = sha256_file(baseline)
    if recorded_hash != current_hash:
        diagnostics.append(
            _error(
                "workspace-baseline-changed",
                "baseline SHA-256 differs from the proposal's recorded "
                "baseline; rebase or replace the proposal",
                baseline,
            )
        )

    if proposal.exists():
        if proposal.read_bytes() == baseline.read_bytes():
            diagnostics.append(
                Diagnostic(
                    Severity.WARN,
                    "workspace-proposal-unchanged",
                    "proposal is identical to baseline",
                    str(proposal),
                )
            )
        diagnostics.extend(lint_file(str(proposal)))

    diagnostics.extend(
        OnboardingStateRule().check_integrity(workspace / "examples")
    )
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a CostFormation build workspace"
    )
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("--record-baseline", action="store_true")
    args = parser.parse_args()
    if args.record_baseline:
        try:
            record_baseline(args.workspace)
        except (FileNotFoundError, OSError, ValueError, YAMLError) as exc:
            print(exc)
            raise SystemExit(2)
    diagnostics = check_workspace(args.workspace)
    errors = sum(item.severity == Severity.ERROR for item in diagnostics)
    warnings = sum(item.severity == Severity.WARN for item in diagnostics)
    if args.format == "json":
        print(
            json.dumps(
                {
                    "diagnostics": [item.to_dict() for item in diagnostics],
                    "summary": {"errors": errors, "warnings": warnings},
                },
                indent=2,
            )
        )
    else:
        for item in diagnostics:
            print(item.human_readable(item.path))
        print(f"{errors} errors, {warnings} warnings")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
