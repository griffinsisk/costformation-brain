#!/usr/bin/env python3
"""Validate distilled, source-linked customer evidence."""

import argparse
import sys
from pathlib import Path
from typing import Any, List

from ruamel.yaml import YAML, YAMLError

REPO_ROOT = str(Path(__file__).resolve().parents[1])
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from validator.diagnostic import Diagnostic, Severity


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "evidence" / "schema.yaml"


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def validate_evidence_file(path: Path) -> List[Diagnostic]:
    yaml = YAML()
    schema = yaml.load(SCHEMA_PATH.read_text())
    try:
        data = yaml.load(path.read_text())
    except (YAMLError, OSError) as exc:
        return [
            Diagnostic(
                Severity.ERROR,
                "evidence-parse-error",
                str(exc),
                str(path),
            )
        ]
    entries = data.get("evidence") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return [
            Diagnostic(
                Severity.ERROR,
                "evidence-root-invalid",
                "'evidence' must be a list",
                str(path),
            )
        ]

    diagnostics: List[Diagnostic] = []
    prohibited = set(schema["prohibited_fields"])
    for index, entry in enumerate(entries):
        location = f"{path}:evidence[{index}]"
        if not isinstance(entry, dict):
            diagnostics.append(
                Diagnostic(
                    Severity.ERROR,
                    "evidence-entry-invalid",
                    "entry must be a mapping",
                    location,
                )
            )
            continue
        for field in schema["required_fields"]:
            if field not in entry or entry[field] in (None, ""):
                diagnostics.append(
                    Diagnostic(
                        Severity.ERROR,
                        "evidence-required-field",
                        f"missing required field '{field}'",
                        location,
                    )
                )
        for key in _walk_keys(entry):
            if key.lower() in prohibited:
                diagnostics.append(
                    Diagnostic(
                        Severity.ERROR,
                        "evidence-prohibited-field",
                        f"prohibited persisted field '{key}'",
                        location,
                    )
                )
        enum_fields = {
            "status": "statuses",
            "confidence": "confidence_values",
            "evidence_type": "evidence_types",
            "customer_scope": "customer_scopes",
            "promotion_status": "promotion_statuses",
        }
        for field, schema_field in enum_fields.items():
            if field in entry and entry[field] not in schema[schema_field]:
                diagnostics.append(
                    Diagnostic(
                        Severity.ERROR,
                        "evidence-enum-invalid",
                        f"invalid {field} '{entry[field]}'",
                        location,
                    )
                )
        if (
            entry.get("status") == "inferred"
            and entry.get("confidence") == "confirmed"
        ):
            diagnostics.append(
                Diagnostic(
                    Severity.ERROR,
                    "evidence-inference-confirmed",
                    "inferred evidence cannot use confirmed confidence",
                    location,
                )
            )
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate distilled evidence YAML")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    diagnostics: List[Diagnostic] = []
    for path in args.files:
        diagnostics.extend(validate_evidence_file(path))
    for item in diagnostics:
        print(item.human_readable(item.path))
    errors = sum(item.severity == Severity.ERROR for item in diagnostics)
    warnings = sum(item.severity == Severity.WARN for item in diagnostics)
    print(f"{errors} errors, {warnings} warnings")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
