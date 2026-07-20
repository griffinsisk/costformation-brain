from pathlib import Path

import pytest

from workspace.init import init_workspace


def _templates(tmp_path: Path) -> Path:
    root = tmp_path / "templates" / "my-org"
    root.mkdir(parents=True)
    (root / "accounts.yaml").write_text("accounts: []\n")
    (root / "tags.yaml").write_text("tags: []\n")
    (root / "dimensions.yaml").write_text("dimensions: []\n")
    (root / "index.yaml").write_text("account_count: 0\n")
    (root / "context.md").write_text("# Customer Context\n")
    return root


def test_init_creates_customer_state_outside_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    workspace = tmp_path / "customer"
    created = init_workspace(workspace, _templates(tmp_path), repo)
    assert workspace / "my-org" / "context.md" in created
    assert (workspace / "context" / "provided").is_dir()
    assert (workspace / "context" / "evidence").is_dir()
    assert (workspace / "context" / "decisions").is_dir()
    assert (workspace / "context" / "index.yaml").exists()
    assert (workspace / ".costformation" / "privacy-policy.yaml").exists()
    assert (
        workspace / ".costformation" / "profile.yaml"
    ).read_text() == "profile: customer\n"
    assert (
        workspace / ".costformation" / "capabilities.yaml"
    ).read_text() == "capabilities: []\n"
    assert "costformation.cz.yaml" in (workspace / ".gitignore").read_text()
    assert "context/" in (workspace / ".gitignore").read_text()
    assert not (repo / "my-org").exists()


def test_init_never_overwrites_customer_context(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    workspace = tmp_path / "customer"
    templates = _templates(tmp_path)
    init_workspace(workspace, templates, repo)
    context = workspace / "my-org" / "context.md"
    context.write_text("# Customer Context\nconfirmed fact\n")
    init_workspace(workspace, templates, repo)
    assert context.read_text().endswith("confirmed fact\n")


def test_init_refuses_repository_destination(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(
        ValueError, match="outside the costformation-brain repository"
    ):
        init_workspace(repo / "customer", _templates(tmp_path), repo)
