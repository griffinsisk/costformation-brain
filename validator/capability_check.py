#!/usr/bin/env python3
"""Validate optional MCP capability manifests."""

import argparse
import sys
from pathlib import Path
from typing import Any, List

from ruamel.yaml import YAML, YAMLError

REPO_ROOT = str(Path(__file__).resolve().parents[1])
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from validator.diagnostic import Diagnostic, Severity


MODEL_PATH = Path(__file__).resolve().parents[1] / "connectors" / "capability-model.yaml"
REQUIRED_FIELDS = ("server", "categories", "access", "status", "auto_select")


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _error(rule_id: str, message: str, location: str) -> Diagnostic:
    return Diagnostic(Severity.ERROR, rule_id, message, location)


def validate_capability_file(path: Path) -> List[Diagnostic]:
    yaml = YAML()
    model = yaml.load(MODEL_PATH.read_text())
    try:
        data = yaml.load(path.read_text())
    except (YAMLError, OSError) as exc:
        return [_error("capability-parse-error", str(exc), str(path))]

    capabilities = data.get("capabilities") if isinstance(data, dict) else None
    if not isinstance(capabilities, list):
        return [
            _error(
                "capability-root-invalid",
                "'capabilities' must be a list",
                str(path),
            )
        ]

    diagnostics: List[Diagnostic] = []
    allowed_categories = set(model["categories"])
    allowed_access = set(model["access_values"])
    allowed_status = set(model["status_values"])
    secret_fields = {field.lower() for field in model["secret_fields"]}

    for index, capability in enumerate(capabilities):
        location = f"{path}:capabilities[{index}]"
        if not isinstance(capability, dict):
            diagnostics.append(
                _error("capability-entry-invalid", "entry must be a mapping", location)
            )
            continue

        for field in REQUIRED_FIELDS:
            if field not in capability or capability[field] in (None, ""):
                diagnostics.append(
                    _error(
                        "capability-required-field",
                        f"missing required field '{field}'",
                        location,
                    )
                )

        categories = capability.get("categories")
        if not isinstance(categories, list) or not categories:
            diagnostics.append(
                _error(
                    "capability-category-invalid",
                    "categories must be a non-empty list",
                    location,
                )
            )
        else:
            for category in categories:
                if category not in allowed_categories:
                    diagnostics.append(
                        _error(
                            "capability-category-invalid",
                            f"unknown capability category '{category}'",
                            location,
                        )
                    )

        access = capability.get("access")
        if access is not None and access not in allowed_access:
            diagnostics.append(
                _error(
                    "capability-access-invalid",
                    f"invalid access value '{access}'",
                    location,
                )
            )
        status = capability.get("status")
        if status is not None and status not in allowed_status:
            diagnostics.append(
                _error(
                    "capability-status-invalid",
                    f"invalid status value '{status}'",
                    location,
                )
            )
        if capability.get("auto_select") is True and access != "read-only":
            diagnostics.append(
                _error(
                    "capability-write-auto-select",
                    "only read-only capabilities may be auto-selected",
                    location,
                )
            )
        for key in _walk_keys(capability):
            if key.lower() in secret_fields:
                diagnostics.append(
                    _error(
                        "capability-secret-field",
                        f"secret field '{key}' is prohibited",
                        location,
                    )
                )
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate optional MCP capability manifests"
    )
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    diagnostics: List[Diagnostic] = []
    for path in args.files:
        diagnostics.extend(validate_capability_file(path))
    for item in diagnostics:
        print(item.human_readable(item.path))
    errors = sum(item.severity == Severity.ERROR for item in diagnostics)
    warnings = sum(item.severity == Severity.WARN for item in diagnostics)
    print(f"{errors} errors, {warnings} warnings")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
