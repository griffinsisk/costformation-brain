"""Telemetry payload validation rules.

Validates records destined for POST /v1/telemetry/{stream_name} against the
rules in telemetry.md and the filter-key syntax in sources.md. These are
pure functions over plain dicts (parsed JSON), not Rule subclasses — telemetry
payloads are not CostFormation dimensions.

Each function returns a list of Diagnostic. `idx` is the 0-based record index
within the payload; it is reported via the `path` field as "records[idx]".
"""
import datetime
import difflib
import re
from typing import List, Optional, Set

from validator.diagnostic import Diagnostic, Severity
from validator.parser import parse_costformation

VALID_GRANULARITIES = {"HOURLY", "DAILY", "MONTHLY"}
REQUIRED_FIELDS = ["timestamp", "granularity", "filter", "element_name", "value"]

# Telemetry filter keys use display-name syntax (sources.md), never
# CostFormation source syntax. e.g. "custom:Environment" not "User:Defined:Environment".
CF_SYNTAX_PREFIXES = ("User:Defined:", "CZ:Defined:", "Tag:", "K8s:")
KNOWN_FILTER_PREFIXES = (
    "custom:", "tag:",
    "k8s_cluster:", "k8s_namespace:", "k8s_workload:", "k8s_label:",
)

_VALUE_RE = re.compile(r"^-?\d+(\.\d+)?$")

_GRANULARITY_STEP = {
    "HOURLY": datetime.timedelta(hours=1),
    "DAILY": datetime.timedelta(days=1),
}


def _diag(severity, rule_id, message, idx):
    return Diagnostic(
        severity=severity,
        rule_id=rule_id,
        message=message,
        path=f"records[{idx}]",
    )


def check_record_fields(record: dict, idx: int) -> List[Diagnostic]:
    """Required fields present, granularity valid, value string-encoded numeric,
    filter is a mapping."""
    diags: List[Diagnostic] = []

    for field in REQUIRED_FIELDS:
        if field not in record:
            diags.append(_diag(
                Severity.ERROR, "telemetry-missing-field",
                f"missing required field '{field}'", idx))
    # Don't pile secondary errors onto a record that is missing fields.
    if diags:
        return diags

    if record["granularity"] not in VALID_GRANULARITIES:
        diags.append(_diag(
            Severity.ERROR, "telemetry-bad-granularity",
            f"granularity '{record['granularity']}' is not one of "
            f"{sorted(VALID_GRANULARITIES)}", idx))

    value = record["value"]
    if not isinstance(value, str) or not _VALUE_RE.match(value):
        diags.append(_diag(
            Severity.ERROR, "telemetry-bad-value",
            f"value must be a string-encoded number (e.g. \"75000\"), "
            f"got {value!r}", idx))

    if not isinstance(record["filter"], dict):
        diags.append(_diag(
            Severity.ERROR, "telemetry-bad-filter",
            f"filter must be a mapping of filter-key -> list of elements, "
            f"got {type(record['filter']).__name__}", idx))

    return diags


def check_timestamp(record: dict, idx: int) -> List[Diagnostic]:
    """ISO 8601, UTC, hourly-aligned (minutes and seconds zero)."""
    raw = record.get("timestamp")
    if not isinstance(raw, str):
        return [_diag(Severity.ERROR, "telemetry-timestamp-invalid",
                      f"timestamp must be an ISO 8601 string, got {raw!r}", idx)]

    # datetime.fromisoformat doesn't accept a trailing Z before 3.11; normalize.
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        ts = datetime.datetime.fromisoformat(normalized)
    except ValueError:
        return [_diag(Severity.ERROR, "telemetry-timestamp-invalid",
                      f"timestamp '{raw}' is not valid ISO 8601", idx)]

    if ts.tzinfo is None or ts.utcoffset() != datetime.timedelta(0):
        return [_diag(Severity.ERROR, "telemetry-timestamp-not-utc",
                      f"timestamp '{raw}' must be UTC ('Z' or '+00:00' offset)", idx)]

    if ts.minute != 0 or ts.second != 0 or ts.microsecond != 0:
        return [_diag(Severity.ERROR, "telemetry-timestamp-not-hourly",
                      f"timestamp '{raw}' is not hourly-aligned — minutes and "
                      f"seconds must be 00:00 (e.g. 2026-06-01T14:00:00Z)", idx)]

    return []


def check_filter_keys(record: dict, idx: int) -> List[Diagnostic]:
    """Filter keys must use telemetry filter-key syntax, values must be lists."""
    diags: List[Diagnostic] = []
    flt = record.get("filter")
    if not isinstance(flt, dict):
        return []  # check_record_fields already reported telemetry-bad-filter

    for key, val in flt.items():
        if any(key.startswith(p) for p in CF_SYNTAX_PREFIXES):
            diags.append(_diag(
                Severity.ERROR, "telemetry-filter-cf-syntax",
                f"filter key '{key}' uses CostFormation source syntax — "
                f"telemetry filter keys use display-name syntax "
                f"(e.g. 'custom:<Dimension Name>', 'tag:<TagName>'); see sources.md",
                idx))
        elif not any(key.startswith(p) for p in KNOWN_FILTER_PREFIXES):
            diags.append(_diag(
                Severity.WARN, "telemetry-filter-unknown-key",
                f"filter key '{key}' does not start with a known telemetry "
                f"filter-key prefix {list(KNOWN_FILTER_PREFIXES)}; verify "
                f"against the filter-key table in sources.md", idx))

        if not isinstance(val, list):
            diags.append(_diag(
                Severity.ERROR, "telemetry-bad-filter",
                f"filter value for '{key}' must be a list of element names, "
                f"got {type(val).__name__}", idx))

    return diags


def extract_element_names(costformation_path: str, dimension_id: str) -> Optional[Set[str]]:
    """Return the static element names (Group rule Names) of *dimension_id*.

    Returns None when the dimension contains GroupBy rules — its elements are
    dynamic and cannot be statically verified.
    Raises ValueError when the dimension does not exist in the file.
    """
    result = parse_costformation(costformation_path)
    if dimension_id not in result.dimensions:
        raise ValueError(
            f"dimension '{dimension_id}' not found in {costformation_path} "
            f"(available: {sorted(result.dimensions)})")

    dim = result.dimensions[dimension_id]
    names: Set[str] = set()
    for rule in dim.get("Rules", []) or []:
        if not isinstance(rule, dict):
            continue
        if rule.get("Type") == "GroupBy":
            return None
        if rule.get("Type") == "Group" and isinstance(rule.get("Name"), str):
            names.add(rule["Name"])
    return names


def check_element_names(records: list, element_names: Set[str]) -> List[Diagnostic]:
    """element_name must exactly (case-sensitively) match a target element."""
    diags: List[Diagnostic] = []
    for idx, record in enumerate(records):
        name = record.get("element_name")
        if not isinstance(name, str) or name in element_names:
            continue
        close = difflib.get_close_matches(name, element_names, n=1)
        hint = f" — did you mean '{close[0]}'? (matching is case-sensitive)" if close else ""
        diags.append(_diag(
            Severity.ERROR, "telemetry-unknown-element",
            f"element_name '{name}' does not match any element of the target "
            f"dimension {sorted(element_names)}{hint}", idx))
    return diags


def _parse_ts(raw):
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        ts = datetime.datetime.fromisoformat(normalized)
    except (ValueError, TypeError, AttributeError):
        return None
    return ts if ts.tzinfo is not None else None


def check_coverage(records: list) -> List[Diagnostic]:
    """WARN on backfill beyond 90 days and on gaps between windows.

    Gaps are tracked per (element_name, granularity) group. MONTHLY records
    are skipped for gap detection (month arithmetic is not worth the
    complexity for a warning; backfill check still applies).
    Records with unparseable timestamps are skipped — check_timestamp
    reports those as errors.
    """
    diags: List[Diagnostic] = []
    now = datetime.datetime.now(datetime.timezone.utc)

    parsed = []
    for rec in records:
        ts = _parse_ts(rec.get("timestamp", ""))
        if ts is not None:
            parsed.append((rec, ts))

    if not parsed:
        return diags

    oldest = min(ts for _, ts in parsed)
    if now - oldest > datetime.timedelta(days=90):
        diags.append(Diagnostic(
            severity=Severity.WARN, rule_id="telemetry-backfill-90d",
            message=f"oldest record is {(now - oldest).days} days old — "
                    f"backfill beyond 90 days requires Enterprise tier "
                    f"(telemetry.md rule 6)",
            path="records"))

    groups: dict = {}
    for rec, ts in parsed:
        key = (rec.get("element_name"), rec.get("granularity"))
        groups.setdefault(key, set()).add(ts)

    for (element, granularity), stamps in sorted(
            groups.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        step = _GRANULARITY_STEP.get(granularity)
        if step is None or len(stamps) < 2:
            continue
        lo, hi = min(stamps), max(stamps)
        expected = set()
        cursor = lo
        while cursor <= hi:
            expected.add(cursor)
            cursor += step
        missing = expected - stamps
        if missing:
            diags.append(Diagnostic(
                severity=Severity.WARN, rule_id="telemetry-window-gap",
                message=f"element '{element}' ({granularity}): {len(missing)} "
                        f"missing window(s) between {lo.isoformat()} and "
                        f"{hi.isoformat()} — costs in uncovered windows fall "
                        f"to DefaultValue (telemetry.md rule 7)",
                path="records"))
    return diags
