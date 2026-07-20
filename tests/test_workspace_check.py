import hashlib
import json
import subprocess
import sys
from pathlib import Path

from validator.workspace_check import check_workspace, sha256_file


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "validator" / "workspace_check.py"
FIXTURES = Path(__file__).parent / "fixtures" / "workspace"


def _make_workspace(tmp_path: Path, recorded_hash: str | None = None) -> Path:
    baseline = tmp_path / "costformation.cz.yaml"
    proposal = tmp_path / "costformation.proposed.cz.yaml"
    baseline.write_text((FIXTURES / "valid-baseline.yaml").read_text())
    proposal.write_text((FIXTURES / "valid-proposal.yaml").read_text())
    digest = recorded_hash or hashlib.sha256(baseline.read_bytes()).hexdigest()
    state_dir = tmp_path / ".costformation"
    state_dir.mkdir()
    (state_dir / "gathering-state.yaml").write_text(
        "workspace:\n"
        "  baseline-path: costformation.cz.yaml\n"
        f"  baseline-sha256: {digest}\n"
        "  proposal-path: costformation.proposed.cz.yaml\n"
    )
    return tmp_path


def _ids(diagnostics):
    return [diagnostic.rule_id for diagnostic in diagnostics]


def test_sha256_file_matches_hashlib(tmp_path):
    path = tmp_path / "value.txt"
    path.write_text("costformation")
    assert sha256_file(path) == hashlib.sha256(path.read_bytes()).hexdigest()


def test_valid_workspace_passes(tmp_path):
    workspace = _make_workspace(tmp_path)
    assert check_workspace(workspace) == []


def test_changed_baseline_is_error(tmp_path):
    workspace = _make_workspace(tmp_path, recorded_hash="0" * 64)
    assert "workspace-baseline-changed" in _ids(check_workspace(workspace))


def test_missing_proposal_is_error(tmp_path):
    workspace = _make_workspace(tmp_path)
    (workspace / "costformation.proposed.cz.yaml").unlink()
    assert "workspace-proposal-missing" in _ids(check_workspace(workspace))


def test_identical_proposal_is_warning(tmp_path):
    workspace = _make_workspace(tmp_path)
    (workspace / "costformation.proposed.cz.yaml").write_bytes(
        (workspace / "costformation.cz.yaml").read_bytes()
    )
    assert "workspace-proposal-unchanged" in _ids(check_workspace(workspace))


def test_workspace_checks_external_onboarding_state(tmp_path):
    workspace = _make_workspace(tmp_path)
    my_org = workspace / "my-org"
    my_org.mkdir()
    (my_org / "onboarding-state.yaml").write_text(
        "phases:\n"
        "  discover:\n"
        "    status: complete\n"
    )
    assert "onboarding-missing-exit-checks" in _ids(check_workspace(workspace))


def test_record_baseline_cli_updates_state(tmp_path):
    workspace = _make_workspace(tmp_path, recorded_hash="0" * 64)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(workspace), "--record-baseline"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "workspace-baseline-changed" not in _ids(check_workspace(workspace))


def test_json_cli_reports_success(tmp_path):
    workspace = _make_workspace(tmp_path)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(workspace), "--format", "json"],
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert result.returncode == 0
    assert data["summary"] == {"errors": 0, "warnings": 0}
