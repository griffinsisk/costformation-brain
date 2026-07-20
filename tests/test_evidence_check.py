from pathlib import Path

from validator.diagnostic import Severity
from validator.evidence_check import validate_evidence_file


FIXTURES = Path(__file__).parent / "fixtures" / "evidence"


def _ids(path: Path):
    return [item.rule_id for item in validate_evidence_file(path)]


def test_valid_distilled_evidence_passes():
    assert validate_evidence_file(FIXTURES / "valid.yaml") == []


def test_raw_transcript_field_is_error():
    diagnostics = validate_evidence_file(FIXTURES / "raw-transcript.yaml")
    assert "evidence-prohibited-field" in [item.rule_id for item in diagnostics]
    assert any(item.severity == Severity.ERROR for item in diagnostics)


def test_inference_cannot_claim_confirmed_confidence(tmp_path):
    text = (FIXTURES / "valid.yaml").read_text().replace(
        "status: customer-confirmed", "status: inferred"
    )
    path = tmp_path / "inferred.yaml"
    path.write_text(text)
    assert "evidence-inference-confirmed" in _ids(path)


def test_missing_provenance_is_error(tmp_path):
    text = (FIXTURES / "valid.yaml").read_text().replace(
        "    source_url: drive://accounts/example/architecture-plan-v2\n", ""
    )
    path = tmp_path / "missing-source.yaml"
    path.write_text(text)
    assert "evidence-required-field" in _ids(path)
