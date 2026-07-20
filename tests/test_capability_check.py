from pathlib import Path

from validator.capability_check import validate_capability_file


FIXTURES = Path(__file__).parent / "fixtures" / "capabilities"


def _ids(path: Path):
    return [item.rule_id for item in validate_capability_file(path)]


def test_valid_read_only_capability_passes():
    assert validate_capability_file(FIXTURES / "valid.yaml") == []


def test_write_capability_cannot_be_auto_selected():
    assert "capability-write-auto-select" in _ids(
        FIXTURES / "write-auto-select.yaml"
    )


def test_unknown_category_is_error(tmp_path):
    text = (FIXTURES / "valid.yaml").read_text().replace(
        "observability", "unknown_vendor_feature"
    )
    path = tmp_path / "unknown.yaml"
    path.write_text(text)
    assert "capability-category-invalid" in _ids(path)


def test_credentials_are_prohibited(tmp_path):
    text = (FIXTURES / "valid.yaml").read_text() + "    api_key: secret\n"
    path = tmp_path / "credentials.yaml"
    path.write_text(text)
    assert "capability-secret-field" in _ids(path)
