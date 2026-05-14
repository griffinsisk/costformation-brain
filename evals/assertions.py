"""Eval assertion module for CostFormation golden-output testing.

Each assertion function receives:
    assertion_dict        — the raw assertion entry from the eval YAML
    dimensions            — the parsed Dimensions mapping from the golden file
    data                  — the full parsed top-level YAML object
    golden_path           — path to the golden YAML file (str)
    validator_diagnostics — List[Diagnostic] from the validator

Returns an AssertionResult.
"""
from __future__ import annotations

import re
import sys
import pathlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ruamel.yaml import YAML

# Ensure repo root is on sys.path for `validator.*` imports when run directly.
_REPO_ROOT = str(pathlib.Path(__file__).parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from validator.diagnostic import Diagnostic  # noqa: E402


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class AssertionResult:
    type: str
    passed: bool
    message: str
    skipped: bool = False


# ---------------------------------------------------------------------------
# Source collection helper
# ---------------------------------------------------------------------------

def _collect_sources(dim_def: Any) -> List[str]:
    """Recursively collect all source strings from a dimension definition.

    Looks at:
    - Dimension-level ``Source`` (str) and ``Sources`` (list)
    - Rule-level ``Source`` (str) and ``Sources`` (list)
    - Condition-level ``Source`` (str or list), recursing through And/Or/Not
    """
    sources: List[str] = []

    if not isinstance(dim_def, dict):
        return sources

    # Dimension-level Source / Sources
    if "Source" in dim_def:
        val = dim_def["Source"]
        if isinstance(val, str):
            sources.append(val)
        elif isinstance(val, list):
            sources.extend(str(v) for v in val)

    if "Sources" in dim_def:
        val = dim_def["Sources"]
        if isinstance(val, list):
            sources.extend(str(v) for v in val)

    # Rules
    rules = dim_def.get("Rules") or []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        # Rule-level Source / Sources
        if "Source" in rule:
            val = rule["Source"]
            if isinstance(val, str):
                sources.append(val)
            elif isinstance(val, list):
                sources.extend(str(v) for v in val)
        if "Sources" in rule:
            val = rule["Sources"]
            if isinstance(val, list):
                sources.extend(str(v) for v in val)
        # Recurse into conditions
        conditions = rule.get("Conditions") or []
        sources.extend(_collect_sources_from_conditions(conditions))

    return sources


def _collect_sources_from_conditions(conditions: Any) -> List[str]:
    """Recursively collect source strings from a conditions block."""
    sources: List[str] = []

    if isinstance(conditions, list):
        for item in conditions:
            sources.extend(_collect_sources_from_conditions(item))
        return sources

    if not isinstance(conditions, dict):
        return sources

    # Condition-level Source (string or list)
    if "Source" in conditions:
        val = conditions["Source"]
        if isinstance(val, str):
            sources.append(val)
        elif isinstance(val, list):
            sources.extend(str(v) for v in val)

    # Recurse through And / Or / Not blocks
    for key in ("And", "Or", "Not"):
        if key in conditions:
            child = conditions[key]
            sources.extend(_collect_sources_from_conditions(child))

    return sources


# ---------------------------------------------------------------------------
# Assertion functions
# ---------------------------------------------------------------------------

def _assert_dimension_exists(
    assertion: Dict,
    dimensions: Dict,
    data: Any,
    golden_path: str,
    validator_diagnostics: List[Diagnostic],
) -> AssertionResult:
    dim_id = assertion.get("id", "")
    passed = dim_id in dimensions
    if passed:
        msg = f"dimension '{dim_id}' exists"
    else:
        msg = f"dimension '{dim_id}' not found in golden output"
    return AssertionResult(type="dimension_exists", passed=passed, message=msg)


def _assert_rule_count(
    assertion: Dict,
    dimensions: Dict,
    data: Any,
    golden_path: str,
    validator_diagnostics: List[Diagnostic],
) -> AssertionResult:
    dim_id = assertion.get("dimension", "")
    dim_def = dimensions.get(dim_id)
    if dim_def is None:
        return AssertionResult(
            type="rule_count",
            passed=False,
            message=f"dimension '{dim_id}' not found",
        )

    rules = dim_def.get("Rules") or []
    count = len(rules)

    min_val: Optional[int] = assertion.get("min")
    max_val: Optional[int] = assertion.get("max")
    equals_val: Optional[int] = assertion.get("equals")

    failures: List[str] = []

    if equals_val is not None and count != equals_val:
        failures.append(f"expected exactly {equals_val} rules, got {count}")
    if min_val is not None and count < min_val:
        failures.append(f"expected at least {min_val} rules, got {count}")
    if max_val is not None and count > max_val:
        failures.append(f"expected at most {max_val} rules, got {count}")

    if failures:
        return AssertionResult(
            type="rule_count",
            passed=False,
            message=f"dimension '{dim_id}': " + "; ".join(failures),
        )
    return AssertionResult(
        type="rule_count",
        passed=True,
        message=f"dimension '{dim_id}' has {count} rule(s)",
    )


def _assert_source_used(
    assertion: Dict,
    dimensions: Dict,
    data: Any,
    golden_path: str,
    validator_diagnostics: List[Diagnostic],
) -> AssertionResult:
    dim_id = assertion.get("dimension", "")
    target_source = assertion.get("source", "")

    dim_def = dimensions.get(dim_id)
    if dim_def is None:
        return AssertionResult(
            type="source_used",
            passed=False,
            message=f"dimension '{dim_id}' not found",
        )

    collected = _collect_sources(dim_def)
    passed = target_source in collected
    if passed:
        msg = f"source '{target_source}' found in dimension '{dim_id}'"
    else:
        msg = (
            f"source '{target_source}' not found in dimension '{dim_id}'; "
            f"sources present: {sorted(set(collected))}"
        )
    return AssertionResult(type="source_used", passed=passed, message=msg)


def _assert_no_default_value(
    assertion: Dict,
    dimensions: Dict,
    data: Any,
    golden_path: str,
    validator_diagnostics: List[Diagnostic],
) -> AssertionResult:
    dim_id = assertion.get("dimension", "")
    dim_def = dimensions.get(dim_id)
    if dim_def is None:
        return AssertionResult(
            type="no_default_value",
            passed=False,
            message=f"dimension '{dim_id}' not found",
        )

    has_default = "DefaultValue" in dim_def
    if has_default:
        val = dim_def["DefaultValue"]
        msg = f"dimension '{dim_id}' has DefaultValue: {val!r}"
    else:
        msg = f"dimension '{dim_id}' has no DefaultValue"
    return AssertionResult(type="no_default_value", passed=not has_default, message=msg)


# Regex that matches a run of 12 digits not surrounded by additional digits.
_TWELVE_DIGITS = re.compile(r"(?<!\d)\d{12}(?!\d)")


def _assert_quoted_account_ids(
    assertion: Dict,
    dimensions: Dict,
    data: Any,
    golden_path: str,
    validator_diagnostics: List[Diagnostic],
) -> AssertionResult:
    """Scan raw file text for unquoted 12-digit account IDs.

    A 12-digit run is considered *unquoted* if it is not immediately preceded
    or followed by a single or double quote character.
    """
    try:
        with open(golden_path, "r") as fh:
            raw_text = fh.read()
    except OSError as exc:
        return AssertionResult(
            type="quoted_account_ids",
            passed=False,
            message=f"could not read golden file: {exc}",
        )

    unquoted: List[str] = []
    for lineno, line in enumerate(raw_text.splitlines(), start=1):
        # Skip comment lines
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue

        for match in _TWELVE_DIGITS.finditer(line):
            start = match.start()
            end = match.end()
            before = line[start - 1] if start > 0 else ""
            after = line[end] if end < len(line) else ""
            if before not in ('"', "'") or after not in ('"', "'"):
                unquoted.append(f"line {lineno}: {match.group()}")

    if unquoted:
        return AssertionResult(
            type="quoted_account_ids",
            passed=False,
            message="unquoted 12-digit account IDs found: " + ", ".join(unquoted),
        )
    return AssertionResult(
        type="quoted_account_ids",
        passed=True,
        message="all 12-digit account IDs are quoted",
    )


def _assert_validator_diagnostics(
    assertion: Dict,
    dimensions: Dict,
    data: Any,
    golden_path: str,
    validator_diagnostics: List[Diagnostic],
) -> AssertionResult:
    severity_filter: Optional[str] = assertion.get("severity")
    rule_id_filter: Optional[str] = assertion.get("rule_id")
    min_val: Optional[int] = assertion.get("min")
    max_val: Optional[int] = assertion.get("max")

    matched = [
        d for d in validator_diagnostics
        if (severity_filter is None or d.severity.value == severity_filter)
        and (rule_id_filter is None or d.rule_id == rule_id_filter)
    ]
    count = len(matched)

    failures: List[str] = []
    if min_val is not None and count < min_val:
        failures.append(f"expected at least {min_val}, got {count}")
    if max_val is not None and count > max_val:
        failures.append(f"expected at most {max_val}, got {count}")

    label_parts: List[str] = []
    if severity_filter:
        label_parts.append(f"severity={severity_filter}")
    if rule_id_filter:
        label_parts.append(f"rule_id={rule_id_filter}")
    label = ", ".join(label_parts) if label_parts else "all"

    if failures:
        return AssertionResult(
            type="validator_diagnostics",
            passed=False,
            message=f"diagnostic count ({label}): " + "; ".join(failures),
        )
    return AssertionResult(
        type="validator_diagnostics",
        passed=True,
        message=f"diagnostic count ({label}) = {count}",
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ASSERTION_REGISTRY: Dict[str, Callable] = {
    "dimension_exists": _assert_dimension_exists,
    "rule_count": _assert_rule_count,
    "source_used": _assert_source_used,
    "no_default_value": _assert_no_default_value,
    "quoted_account_ids": _assert_quoted_account_ids,
    "validator_diagnostics": _assert_validator_diagnostics,
}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_assertions(
    assertions: List[Dict],
    golden_path: str,
    validator_diagnostics: List[Diagnostic],
) -> List[AssertionResult]:
    """Load the golden YAML, run each assertion, and return all results.

    Args:
        assertions:             List of assertion dicts from the eval spec.
        golden_path:            Path to the golden CostFormation YAML file.
        validator_diagnostics:  Diagnostics produced by running the validator
                                against the golden file.

    Returns:
        A list of :class:`AssertionResult` objects, one per assertion entry.
        Unknown assertion types produce a result with ``skipped=True``.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    try:
        with open(golden_path, "r") as fh:
            data = yaml.load(fh)
    except Exception as exc:
        # Return a single failed result so callers get a meaningful error.
        return [
            AssertionResult(
                type="load_golden",
                passed=False,
                message=f"failed to load golden file '{golden_path}': {exc}",
            )
        ]

    dimensions: Dict = {}
    if isinstance(data, dict):
        dimensions = data.get("Dimensions") or {}

    results: List[AssertionResult] = []
    for assertion in assertions:
        atype = assertion.get("type", "")
        handler = ASSERTION_REGISTRY.get(atype)
        if handler is None:
            results.append(
                AssertionResult(
                    type=atype,
                    passed=True,
                    message="unknown type — skipped",
                    skipped=True,
                )
            )
            continue
        result = handler(assertion, dimensions, data, golden_path, validator_diagnostics)
        results.append(result)

    return results
