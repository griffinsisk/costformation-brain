"""Tests for telemetry payload validation rules."""
import pytest

from validator.rules.telemetry import (
    check_record_fields,
    check_timestamp,
)
from validator.diagnostic import Severity


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
