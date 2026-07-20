#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from validator.capability_check import validate_capability_file
from validator.diagnostic import Severity


CASES_DIR = REPO_ROOT / "evals" / "harness_cases"
EVALS_DIR = REPO_ROOT / "evals"


def resolve_path(value: Any, dotted_path: str) -> Any:
    current = value
    for part in dotted_path.split("."):
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def assertion_passes(data: Any, assertion: dict) -> bool:
    actual = resolve_path(data, assertion["path"])
    if "equals" in assertion:
        return actual == assertion["equals"]
    if "contains" in assertion:
        return assertion["contains"] in actual
    raise ValueError(f"unsupported assertion: {assertion}")


def main() -> None:
    yaml = YAML()
    cases = sorted(CASES_DIR.glob("*.yaml"))
    passed = 0
    for case_path in cases:
        case = yaml.load(case_path.read_text())
        golden_path = EVALS_DIR / case["golden_output"]
        golden = yaml.load(golden_path.read_text())
        diagnostics = validate_capability_file(golden_path)
        no_errors = not any(item.severity == Severity.ERROR for item in diagnostics)
        assertions_ok = all(
            assertion_passes(golden, assertion)
            for assertion in case.get("assertions") or []
        )
        ok = no_errors and assertions_ok
        print(f"{'PASS' if ok else 'FAIL'}  {case['test_id']}")
        if ok:
            passed += 1
    print(f"{passed}/{len(cases)} passed")
    raise SystemExit(0 if passed == len(cases) else 1)


if __name__ == "__main__":
    main()
