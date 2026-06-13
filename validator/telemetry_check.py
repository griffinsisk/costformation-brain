#!/usr/bin/env python3
"""CLI for validating CloudZero telemetry payloads before sending.

Usage:
    python3 validator/telemetry_check.py PAYLOAD.json
        [--costformation FILE --target-dimension DIM_ID]
        [--format human|json]

PAYLOAD.json is either {"records": [...]} (the API POST body) or a bare
JSON list of records.

Exit codes (mirrors lint.py):
    0 — no errors (warnings may be present)
    1 — one or more errors found
    2 — usage error (bad arguments, unreadable payload, unknown dimension)
"""
import argparse
import json
import pathlib
import sys
from typing import List

_REPO_ROOT = str(pathlib.Path(__file__).parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from validator.diagnostic import Diagnostic, Severity
from validator.rules.telemetry import (
    check_coverage,
    check_element_names,
    check_filter_keys,
    check_record_fields,
    check_timestamp,
    extract_element_names,
)


def check_payload(records: list) -> List[Diagnostic]:
    diagnostics: List[Diagnostic] = []
    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            diagnostics.append(Diagnostic(
                severity=Severity.ERROR, rule_id="telemetry-bad-record",
                message=f"record must be an object, got {type(record).__name__}",
                path=f"records[{idx}]"))
            continue
        diagnostics.extend(check_record_fields(record, idx))
        diagnostics.extend(check_timestamp(record, idx))
        diagnostics.extend(check_filter_keys(record, idx))
    diagnostics.extend(check_coverage([r for r in records if isinstance(r, dict)]))
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a telemetry payload against telemetry.md rules.",
        prog="telemetry_check.py")
    parser.add_argument("payload", metavar="PAYLOAD",
                        help="JSON file: {'records': [...]} or a bare list.")
    parser.add_argument("--costformation", metavar="FILE",
                        help="CostFormation YAML containing the target dimension.")
    parser.add_argument("--target-dimension", metavar="DIM_ID",
                        help="Dimension ID whose elements element_name must match.")
    parser.add_argument("--format", choices=["human", "json"], default="human")
    args = parser.parse_args()

    if bool(args.costformation) != bool(args.target_dimension):
        sys.stderr.write("error: --costformation and --target-dimension "
                         "must be used together\n")
        sys.exit(2)

    try:
        with open(args.payload) as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"error: cannot read payload: {exc}\n")
        sys.exit(2)

    records = data.get("records") if isinstance(data, dict) else data
    if not isinstance(records, list):
        sys.stderr.write("error: payload must be {'records': [...]} or a list\n")
        sys.exit(2)

    diagnostics = check_payload(records)
    notes: List[str] = []

    if args.costformation:
        try:
            elements = extract_element_names(args.costformation,
                                             args.target_dimension)
        except (ValueError, OSError) as exc:
            sys.stderr.write(f"error: {exc}\n")
            sys.exit(2)
        if elements is None:
            notes.append(
                f"note: dimension '{args.target_dimension}' uses GroupBy rules — "
                f"elements are dynamic, element_name check skipped")
        else:
            diagnostics.extend(check_element_names(
                [r for r in records if isinstance(r, dict)], elements))

    errors = sum(1 for d in diagnostics if d.severity == Severity.ERROR)
    warnings = sum(1 for d in diagnostics if d.severity == Severity.WARN)

    if args.format == "json":
        print(json.dumps({
            "file": args.payload,
            "diagnostics": [d.to_dict() for d in diagnostics],
            "notes": notes,
            "summary": {"errors": errors, "warnings": warnings,
                        "records_checked": len(records)},
        }, indent=2))
    else:
        for d in diagnostics:
            print(d.human_readable(args.payload))
        for note in notes:
            print(note)
        status = "OK" if errors == 0 else "FAIL"
        print(f"{status}: {len(records)} record{'s' if len(records) != 1 else ''}, "
              f"{errors} error{'s' if errors != 1 else ''}, "
              f"{warnings} warning{'s' if warnings != 1 else ''}")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
