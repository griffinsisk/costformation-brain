#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path
from typing import List


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = REPO_ROOT / "workspace" / "templates" / "my-org"
MY_ORG_FILES = (
    "accounts.yaml",
    "tags.yaml",
    "dimensions.yaml",
    "index.yaml",
    "context.md",
)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def init_workspace(
    workspace: Path,
    template_root: Path = TEMPLATE_ROOT,
    repo_root: Path = REPO_ROOT,
) -> List[Path]:
    workspace = workspace.resolve()
    if _is_within(workspace, repo_root):
        raise ValueError(
            "customer workspace must be outside the costformation-brain repository"
        )

    created: List[Path] = []
    my_org = workspace / "my-org"
    my_org.mkdir(parents=True, exist_ok=True)
    for filename in MY_ORG_FILES:
        destination = my_org / filename
        if not destination.exists():
            shutil.copy2(template_root / filename, destination)
            created.append(destination)

    for relative in (
        Path("context/provided"),
        Path("context/evidence"),
        Path("context/decisions"),
        Path("context/collectors"),
        Path(".costformation"),
    ):
        directory = workspace / relative
        if not directory.exists():
            directory.mkdir(parents=True)
            created.append(directory)

    privacy_policy = workspace / ".costformation" / "privacy-policy.yaml"
    if not privacy_policy.exists():
        privacy_policy.write_text(
            "version: 1\n"
            "persist_raw_transcripts: false\n"
            "persist_complete_mcp_responses: false\n"
            "external_writes_require_approval: true\n"
            "allow_customer_data_in_repositories: false\n"
        )
        created.append(privacy_policy)

    initial_files = {
        workspace / ".costformation" / "profile.yaml": "profile: customer\n",
        workspace / ".costformation" / "capabilities.yaml": "capabilities: []\n",
        workspace / ".costformation" / "gathering-state.yaml": (
            "workspace:\n"
            "  baseline-path: costformation.cz.yaml\n"
            "  baseline-sha256: null\n"
            "  proposal-path: costformation.proposed.cz.yaml\n"
        ),
        workspace / "context" / "index.yaml": (
            "version: 1\n"
            "last-updated: null\n"
            "evidence-files: []\n"
            "decision-files: []\n"
        ),
    }
    for destination, content in initial_files.items():
        if not destination.exists():
            destination.write_text(content)
            created.append(destination)

    gitignore = workspace / ".gitignore"
    ignore_entries = (
        "my-org/",
        "context/",
        ".costformation/",
        "costformation.cz.yaml",
        "costformation.proposed.cz.yaml",
    )
    existing = gitignore.read_text().splitlines() if gitignore.exists() else []
    missing = [entry for entry in ignore_entries if entry not in existing]
    if missing:
        current = gitignore.read_text() if gitignore.exists() else ""
        prefix = "\n" if current and not current.endswith("\n") else ""
        with gitignore.open("a") as handle:
            handle.write(prefix + "\n".join(missing) + "\n")
        created.append(gitignore)
    return created


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize a customer-safe CostFormation workspace"
    )
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    for path in init_workspace(args.workspace):
        print(path)


if __name__ == "__main__":
    main()
