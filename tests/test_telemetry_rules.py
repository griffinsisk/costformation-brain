"""Tests for telemetry payload validation rules."""
import datetime
import pathlib

import pytest

from validator.rules.telemetry import (
    check_record_fields,
    check_timestamp,
    check_filter_keys,
    check_element_names,
    extract_element_names,
    check_coverage,
)
from validator.diagnostic import Severity

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
TARGET_YAML = str(FIXTURES / "telemetry_target.yaml")


GOOD_RECORD = {
    "timestamp": "2026-06-01T14:00:00Z",
    "granularity": "HOURLY",
    "filter": {"custom:Spend Category": ["Shared"]},
    "element_name": "Team-Alpha",
    "value": "75000",
}


def _ids(diags):
    return [d.rule_id for d in diags]


def test_good_record_has_no_field_diagnostics():
    assert check_record_fields(GOOD_RECORD, 0) == []


def test_missing_field_is_error():
    rec = {k: v for k, v in GOOD_RECORD.items() if k != "element_name"}
    diags = check_record_fields(rec, 0)
    assert "telemetry-missing-field" in _ids(diags)
    assert all(d.severity == Severity.ERROR for d in diags)


def test_bad_granularity_is_error():
    rec = dict(GOOD_RECORD, granularity="WEEKLY")
    assert "telemetry-bad-granularity" in _ids(check_record_fields(rec, 0))


def test_numeric_value_is_error():
    # telemetry.md: value must be a STRING-encoded number
    rec = dict(GOOD_RECORD, value=75000)
    assert "telemetry-bad-value" in _ids(check_record_fields(rec, 0))


def test_non_numeric_string_value_is_error():
    rec = dict(GOOD_RECORD, value="lots")
    assert "telemetry-bad-value" in _ids(check_record_fields(rec, 0))


def test_filter_not_dict_is_error():
    rec = dict(GOOD_RECORD, filter="custom:Spend Category")
    assert "telemetry-bad-filter" in _ids(check_record_fields(rec, 0))


def test_good_timestamp_passes():
    assert check_timestamp(GOOD_RECORD, 0) == []


def test_unparseable_timestamp_is_error():
    rec = dict(GOOD_RECORD, timestamp="June 1st 2026")
    assert "telemetry-timestamp-invalid" in _ids(check_timestamp(rec, 0))


def test_non_utc_timestamp_is_error():
    rec = dict(GOOD_RECORD, timestamp="2026-06-01T14:00:00-05:00")
    assert "telemetry-timestamp-not-utc" in _ids(check_timestamp(rec, 0))


def test_naive_timestamp_is_error():
    rec = dict(GOOD_RECORD, timestamp="2026-06-01T14:00:00")
    assert "telemetry-timestamp-not-utc" in _ids(check_timestamp(rec, 0))


def test_non_hourly_aligned_is_error():
    # The silent killer: minutes/seconds must be 00:00
    rec = dict(GOOD_RECORD, timestamp="2026-06-01T14:23:11Z")
    assert "telemetry-timestamp-not-hourly" in _ids(check_timestamp(rec, 0))


def test_plus_zero_offset_is_accepted_as_utc():
    rec = dict(GOOD_RECORD, timestamp="2026-06-01T14:00:00+00:00")
    assert check_timestamp(rec, 0) == []


# ---------------------------------------------------------------------------
# Task 2: Filter-key syntax
# ---------------------------------------------------------------------------

def test_custom_and_tag_filter_keys_pass():
    rec = dict(GOOD_RECORD, filter={
        "custom:Spend Category": ["Shared"],
        "tag:environment": ["prod"],
        "k8s_namespace:payments": ["payments"],
    })
    assert check_filter_keys(rec, 0) == []


def test_costformation_syntax_in_filter_is_error():
    # The known failure mode: CF source syntax instead of telemetry filter keys
    for bad_key in ("User:Defined:SpendCategory", "CZ:Defined:GenAI_Model",
                    "Tag:environment", "K8s:Namespace"):
        rec = dict(GOOD_RECORD, filter={bad_key: ["Shared"]})
        diags = check_filter_keys(rec, 0)
        assert "telemetry-filter-cf-syntax" in _ids(diags), bad_key
        assert diags[0].severity == Severity.ERROR


def test_unknown_filter_prefix_is_warning():
    rec = dict(GOOD_RECORD, filter={"dimension:Spend Category": ["Shared"]})
    diags = check_filter_keys(rec, 0)
    assert "telemetry-filter-unknown-key" in _ids(diags)
    assert diags[0].severity == Severity.WARN


def test_filter_value_not_list_is_error():
    rec = dict(GOOD_RECORD, filter={"custom:Spend Category": "Shared"})
    assert "telemetry-filter-cf-syntax" not in _ids(check_filter_keys(rec, 0))
    assert any(d.rule_id == "telemetry-bad-filter" for d in check_filter_keys(rec, 0))


# ---------------------------------------------------------------------------
# Task 3: Element-name cross-check
# ---------------------------------------------------------------------------

def test_extract_element_names_from_group_rules():
    names = extract_element_names(TARGET_YAML, "SpendCategory")
    assert names == {"Team-Alpha", "Team-Beta", "Shared"}


def test_extract_returns_none_for_groupby_dimension():
    # GroupBy elements are dynamic — cannot be statically verified
    assert extract_element_names(TARGET_YAML, "DynamicTeams") is None


def test_extract_unknown_dimension_raises():
    with pytest.raises(ValueError):
        extract_element_names(TARGET_YAML, "Nope")


def test_known_element_passes():
    assert check_element_names([GOOD_RECORD], {"Team-Alpha", "Team-Beta"}) == []


def test_unknown_element_is_error_with_suggestion():
    rec = dict(GOOD_RECORD, element_name="team-alpha")  # wrong case
    diags = check_element_names([rec], {"Team-Alpha", "Team-Beta"})
    assert _ids(diags) == ["telemetry-unknown-element"]
    assert "Team-Alpha" in diags[0].message  # close-match suggestion


# ---------------------------------------------------------------------------
# Task 4: Coverage warnings
# ---------------------------------------------------------------------------

def _rec(ts, element="Team-Alpha", granularity="HOURLY"):
    return dict(GOOD_RECORD, timestamp=ts, element_name=element,
                granularity=granularity)


def test_recent_contiguous_records_have_no_warnings():
    now = datetime.datetime.now(datetime.timezone.utc).replace(
        minute=0, second=0, microsecond=0)
    recs = [_rec((now - datetime.timedelta(hours=h)).strftime("%Y-%m-%dT%H:00:00Z"))
            for h in range(1, 4)]
    assert check_coverage(recs) == []


def test_backfill_beyond_90_days_warns():
    old = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=120)
    recs = [_rec(old.strftime("%Y-%m-%dT%H:00:00Z"))]
    diags = check_coverage(recs)
    assert "telemetry-backfill-90d" in _ids(diags)
    assert all(d.severity == Severity.WARN for d in diags)


def test_gap_in_hourly_windows_warns():
    recs = [_rec("2026-06-01T10:00:00Z"), _rec("2026-06-01T14:00:00Z")]
    diags = check_coverage(recs)
    gap = [d for d in diags if d.rule_id == "telemetry-window-gap"]
    assert len(gap) == 1
    assert "3 missing" in gap[0].message  # 11:00, 12:00, 13:00


def test_gaps_tracked_per_element():
    # Each element has contiguous coverage; no cross-element false positive
    recs = [_rec("2026-06-01T10:00:00Z", "Team-Alpha"),
            _rec("2026-06-01T11:00:00Z", "Team-Alpha"),
            _rec("2026-06-01T14:00:00Z", "Team-Beta")]
    assert [d for d in check_coverage(recs)
            if d.rule_id == "telemetry-window-gap"] == []


def test_daily_gap_warns():
    recs = [_rec("2026-06-01T00:00:00Z", granularity="DAILY"),
            _rec("2026-06-03T00:00:00Z", granularity="DAILY")]
    diags = check_coverage(recs)
    assert "telemetry-window-gap" in _ids(diags)
