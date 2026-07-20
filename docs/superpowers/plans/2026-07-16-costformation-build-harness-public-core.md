# CostFormation Build Harness Public Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the public `costformation-brain` repository into the customer-safe foundation of a profile-aware CostFormation build harness.

**Architecture:** Keep the existing markdown-driven corpus and Python validator model. Add deterministic workspace, evidence, and capability checks around it, then route customer agents through generic MCP discovery and a two-file baseline/proposal lifecycle. The private `costformation-se` repository is a separate implementation plan after this public compatibility contract ships.

**Tech Stack:** Python 3.10+, `ruamel.yaml`, `pytest`, Markdown agent instructions, YAML schemas and fixtures.

## Global Constraints

- Never edit `costformation.cz.yaml`.
- Never publish to CloudZero.
- Never persist raw meeting transcripts or complete MCP responses.
- Never invoke an external write operation without explicit approval.
- Never write customer-specific artifacts inside this repository.
- Never promote a customer fact into shared knowledge automatically.
- `costformation.proposed.cz.yaml` is the only generated CostFormation working file and contains the complete definition.
- Customer-facing runtime and setup files must not mention Salesforce, Granola, Sybill, or CloudZero-internal sales processes.
- Optional MCPs are classified by capability, not by a hard-coded vendor catalog.
- Python changes are test-first and introduce no dependency beyond the existing `ruamel.yaml` and `pytest` requirements.

---

## Scope Split

This plan implements only the public repository. After it is complete, create a
second plan inside the private `costformation-se` repository for:

- `cz-pov init` and workspace health commands;
- SE-profile instruction composition;
- Salesforce account/opportunity resolution;
- Granola and Sybill in-memory distillation;
- public-core compatibility enforcement; and
- reviewed anonymized-learning export.

The private plan consumes the public contracts defined here; it must not copy or
fork their implementations.

## File Map

### New runtime files

- `workspace/two-file-workflow.md` — normative baseline/proposal lifecycle.
- `profiles/customer.md` — customer-safe gathering and build orchestration.
- `connectors/capability-model.yaml` — allowed capability, access, and status values.
- `connectors/discovery.md` — generic MCP inventory and conservative classification procedure.
- `connectors/query-strategy.md` — capability-to-question routing and source precedence.
- `evidence/schema.yaml` — evidence envelope contract.
- `evidence/authority.md` — epistemic status, freshness, contradiction, and promotion rules.
- `validator/workspace_check.py` — deterministic workspace drift and proposal validator.
- `validator/evidence_check.py` — deterministic distilled-evidence validator.
- `validator/capability_check.py` — deterministic capability-manifest validator.

### New tests and fixtures

- `tests/test_workspace_check.py`
- `tests/test_evidence_check.py`
- `tests/test_capability_check.py`
- `tests/test_harness_instruction_consistency.py`
- `tests/fixtures/workspace/valid-baseline.yaml`
- `tests/fixtures/workspace/valid-proposal.yaml`
- `tests/fixtures/evidence/valid.yaml`
- `tests/fixtures/evidence/raw-transcript.yaml`
- `tests/fixtures/capabilities/valid.yaml`
- `tests/fixtures/capabilities/write-auto-select.yaml`

### Existing files to modify

- `SKILL.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.cursorrules`
- `.github/copilot-instructions.md`
- `README.md`
- `onboarding/journey.md`
- `onboarding/phase-2-dimensions.md`
- `onboarding/phase-4-allocation.md`
- `validator/lint.py`
- `tests/test_lint_cli.py`

---

### Task 1: Replace the backup/change-folder contract with the two-file contract

**Files:**

- Create: `workspace/two-file-workflow.md`
- Create: `tests/test_harness_instruction_consistency.py`
- Modify: `SKILL.md`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Modify: `.cursorrules`
- Modify: `.github/copilot-instructions.md`
- Modify: `onboarding/journey.md`
- Modify: `onboarding/phase-2-dimensions.md`
- Modify: `onboarding/phase-4-allocation.md`

**Interfaces:**

- Consumes: existing instruction-file routing and CostFormation validator command.
- Produces: one normative `workspace/two-file-workflow.md` contract referenced by every agent instruction file.

- [ ] **Step 1: Write the failing consistency tests**

Create `tests/test_harness_instruction_consistency.py`:

```python
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTRUCTION_FILES = [
    REPO_ROOT / "SKILL.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / ".cursorrules",
    REPO_ROOT / ".github" / "copilot-instructions.md",
]
ONBOARDING_FILES = [
    REPO_ROOT / "onboarding" / "journey.md",
    REPO_ROOT / "onboarding" / "phase-2-dimensions.md",
    REPO_ROOT / "onboarding" / "phase-4-allocation.md",
]
FORBIDDEN_WORKFLOW_PHRASES = [
    "timestamped backup",
    "timestamped copy",
    "change sub-folder",
    "change folder",
    "_comments.md",
]


def test_all_instruction_files_route_to_two_file_workflow():
    for path in INSTRUCTION_FILES:
        text = path.read_text()
        assert "workspace/two-file-workflow.md" in text, path
        assert "costformation.proposed.cz.yaml" in text, path


def test_old_working_file_contract_is_removed():
    for path in INSTRUCTION_FILES + ONBOARDING_FILES:
        lowered = path.read_text().lower()
        for phrase in FORBIDDEN_WORKFLOW_PHRASES:
            assert phrase.lower() not in lowered, f"{path}: {phrase}"


def test_production_baseline_is_declared_immutable():
    for path in INSTRUCTION_FILES:
        text = path.read_text()
        assert "Never edit `costformation.cz.yaml`" in text, path
```

- [ ] **Step 2: Run the tests and verify the old contract fails**

Run:

```bash
python3 -m pytest tests/test_harness_instruction_consistency.py -v
```

Expected: FAIL because the instruction files still require timestamped backups
and do not route to `workspace/two-file-workflow.md`.

- [ ] **Step 3: Add the normative workflow document**

Create `workspace/two-file-workflow.md` with this complete contract:

```markdown
# Two-File CostFormation Workflow

The workspace has one immutable baseline and one complete proposal:

- `costformation.cz.yaml` — the latest definition downloaded through the
  CloudZero VS Code Toolkit. Never edit this file.
- `costformation.proposed.cz.yaml` — the only CostFormation working file. It
  contains the complete proposed definition, not a dimension snippet.

Before building:

1. Confirm `costformation.cz.yaml` is the latest downloaded definition.
2. If no proposal exists, copy the complete baseline to
   `costformation.proposed.cz.yaml` and edit only the proposal.
3. If a proposal exists and differs from the baseline, show a concise diff and
   ask whether to retain, replace, or rebase it. Never overwrite it silently.
4. Record the baseline SHA-256 used by the proposal in
   `.costformation/gathering-state.yaml`.

Before handoff:

1. Verify the current baseline SHA-256 matches the proposal's recorded
   `baseline-sha256`.
2. Run `python3 costformation-brain/validator/workspace_check.py .`.
3. Fix every ERROR before presenting the proposal as publish-ready.
4. Summarize the baseline-to-proposal diff and any remaining WARNINGs.

Publishing is always a deliberate human action through the CloudZero VS Code
Toolkit. The harness never edits the baseline and never publishes.
```

- [ ] **Step 4: Replace the working-file sections in all instruction files**

In `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, and
`.github/copilot-instructions.md`, replace the existing backup/change-folder
section with this exact text:

```markdown
## Two-File CostFormation Workflow

Always read `costformation-brain/workspace/two-file-workflow.md` before changing
CostFormation.

- Never edit `costformation.cz.yaml`; it is the latest downloaded baseline.
- Make changes only in the complete `costformation.proposed.cz.yaml` file.
- If an existing proposal differs from the baseline, ask whether to retain,
  replace, or rebase it. Never overwrite it silently.
- Validate with `python3 costformation-brain/validator/workspace_check.py .`
  before handoff.
- Never publish; the user publishes through the CloudZero VS Code Toolkit.
```

Replace `SKILL.md` lines 47–48 with:

```markdown
**Before changing any costformation file:**
7. Read `workspace/two-file-workflow.md`. Never edit
   `costformation.cz.yaml`; create or update the complete
   `costformation.proposed.cz.yaml` proposal and preserve any divergent
   existing proposal until the user chooses retain, replace, or rebase.
```

Replace `SKILL.md`'s post-generation validator steps with:

```markdown
**After generating or modifying CostFormation YAML:**
8. Run `python3 costformation-brain/validator/workspace_check.py .`.
9. Fix all ERRORs before presenting the proposal. Do not show a proposal with
   validator errors as publish-ready.
10. Briefly summarize the baseline-to-proposal diff and remaining WARNINGs.
```

- [ ] **Step 5: Update onboarding artifact paths**

Make these exact policy changes:

- `onboarding/journey.md`: replace references to timestamped backups and change
  folders with `costformation.proposed.cz.yaml`; keep `artifacts` for genuine
  non-CostFormation outputs such as telemetry collectors.
- `onboarding/phase-2-dimensions.md`: record
  `costformation.proposed.cz.yaml` as the phase's CostFormation artifact.
- `onboarding/phase-4-allocation.md`: put generated collectors under
  `context/collectors/<stream-name>.py`; record that path as an artifact; use
  `costformation.proposed.cz.yaml` for the allocation definition.

Use this wording wherever the onboarding docs describe CostFormation output:

```markdown
Build the complete change in `costformation.proposed.cz.yaml` using the latest
`costformation.cz.yaml` as its immutable baseline. Validate the complete
proposal with `validator/workspace_check.py`; do not create dimension snippets,
backup files, or per-change comments files.
```

- [ ] **Step 6: Run the consistency tests**

Run:

```bash
python3 -m pytest tests/test_harness_instruction_consistency.py -v
```

Expected: 3 passed.

- [ ] **Step 7: Commit the contract change**

```bash
git add SKILL.md AGENTS.md CLAUDE.md .cursorrules .github/copilot-instructions.md workspace/two-file-workflow.md onboarding/journey.md onboarding/phase-2-dimensions.md onboarding/phase-4-allocation.md tests/test_harness_instruction_consistency.py
git commit -m "feat: adopt two-file CostFormation workflow"
```

---

### Task 2: Externalize customer state from the repository

**Files:**

- Create: `workspace/init.py`
- Create: `tests/test_workspace_init.py`
- Move: `my-org/accounts.yaml` → `workspace/templates/my-org/accounts.yaml`
- Move: `my-org/tags.yaml` → `workspace/templates/my-org/tags.yaml`
- Move: `my-org/dimensions.yaml` → `workspace/templates/my-org/dimensions.yaml`
- Move: `my-org/index.yaml` → `workspace/templates/my-org/index.yaml`
- Move: `my-org/context.md` → `workspace/templates/my-org/context.md`
- Modify: `SKILL.md`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Modify: `.cursorrules`
- Modify: `.github/copilot-instructions.md`
- Modify: `README.md`
- Modify: `onboarding/journey.md`
- Modify: `onboarding/phase-1-discover.md`

**Interfaces:**

- Consumes: the tracked, customer-empty templates under
  `workspace/templates/my-org/`.
- Produces: `init_workspace(workspace: Path, template_root: Path = TEMPLATE_ROOT,
  repo_root: Path = REPO_ROOT) -> list[Path]`, which creates customer state only
  in the workspace containing the `costformation-brain` clone.

- [ ] **Step 1: Write failing workspace-initialization tests**

Create `tests/test_workspace_init.py`:

```python
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
    assert (workspace / ".costformation" / "profile.yaml").read_text() == "profile: customer\n"
    assert (workspace / ".costformation" / "capabilities.yaml").read_text() == "capabilities: []\n"
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
    with pytest.raises(ValueError, match="outside the costformation-brain repository"):
        init_workspace(repo / "customer", _templates(tmp_path), repo)
```

- [ ] **Step 2: Run the tests and verify the initializer is missing**

Run:

```bash
python3 -m pytest tests/test_workspace_init.py -v
```

Expected: collection ERROR with `ModuleNotFoundError: workspace.init`.

- [ ] **Step 3: Move customer-empty templates**

Run:

```bash
mkdir -p workspace/templates/my-org
git mv my-org/accounts.yaml workspace/templates/my-org/accounts.yaml
git mv my-org/tags.yaml workspace/templates/my-org/tags.yaml
git mv my-org/dimensions.yaml workspace/templates/my-org/dimensions.yaml
git mv my-org/index.yaml workspace/templates/my-org/index.yaml
git mv my-org/context.md workspace/templates/my-org/context.md
```

Do not move a populated customer file. Before each `git mv`, confirm the source
still contains only repository defaults and no customer identifiers.

- [ ] **Step 4: Implement the public workspace initializer**

Create `workspace/init.py`:

```python
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
        raise ValueError("customer workspace must be outside the costformation-brain repository")

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
        prefix = "\n" if gitignore.exists() and gitignore.read_text() and not gitignore.read_text().endswith("\n") else ""
        with gitignore.open("a") as handle:
            handle.write(prefix + "\n".join(missing) + "\n")
        created.append(gitignore)
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a customer-safe CostFormation workspace")
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    for path in init_workspace(args.workspace):
        print(path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Route all customer context references to the workspace root**

In `SKILL.md`, all agent instruction files, `README.md`, and onboarding docs,
define `my-org/` as a sibling of `costformation-brain/` under the customer
workspace. Replace any instruction that writes
`costformation-brain/my-org/<file>` with `my-org/<file>`.

Add this exact invariant to each agent instruction file:

```markdown
Customer-specific documents, `my-org/`, `context/`, `.costformation/`, and both
CostFormation definition files live in the customer workspace outside the
`costformation-brain` repository. Never write customer data inside either Git
repository.
```

Update public setup in `README.md` to run:

```bash
python3 costformation-brain/workspace/init.py .
```

from the customer folder after cloning the core.

- [ ] **Step 6: Run initializer and instruction tests**

Run:

```bash
python3 -m pytest tests/test_workspace_init.py tests/test_harness_instruction_consistency.py -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit customer-state isolation**

```bash
git add workspace tests/test_workspace_init.py SKILL.md AGENTS.md CLAUDE.md .cursorrules .github/copilot-instructions.md README.md onboarding/journey.md onboarding/phase-1-discover.md
git commit -m "feat: keep customer state outside repository"
```

---

### Task 3: Add deterministic workspace and proposal validation

**Files:**

- Create: `validator/workspace_check.py`
- Create: `tests/test_workspace_check.py`
- Create: `tests/fixtures/workspace/valid-baseline.yaml`
- Create: `tests/fixtures/workspace/valid-proposal.yaml`
- Modify: `README.md`

**Interfaces:**

- Consumes: `validator.lint.lint_file(filepath: str) -> list[Diagnostic]`.
- Produces: `sha256_file(path: Path) -> str`,
  `record_baseline(workspace: Path) -> str`,
  `check_workspace(workspace: Path) -> list[Diagnostic]`, and CLI
  `python3 validator/workspace_check.py <workspace> [--record-baseline]
  [--format human|json]`.

- [ ] **Step 1: Add valid CostFormation fixtures**

Create both fixture files with the following baseline content:

```yaml
Dimensions:
  Environment:
    Name: Environment
    Hide: true
    Source: Tag:environment
    Transforms:
      - Type: Lower
    Rules:
      - Type: GroupBy
```

In `tests/fixtures/workspace/valid-proposal.yaml`, add this dimension after
`Environment`:

```yaml
  Team:
    Name: Team
    Hide: true
    Source: Tag:team
    Transforms:
      - Type: Lower
    Rules:
      - Type: GroupBy
```

- [ ] **Step 2: Write failing unit and CLI tests**

Create `tests/test_workspace_check.py`:

```python
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
```

- [ ] **Step 3: Run the tests and verify the module is missing**

Run:

```bash
python3 -m pytest tests/test_workspace_check.py -v
```

Expected: collection ERROR with `ModuleNotFoundError: validator.workspace_check`.

- [ ] **Step 4: Implement `validator/workspace_check.py`**

Implement these exact behaviors:

```python
#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import List

from ruamel.yaml import YAML, YAMLError

REPO_ROOT = str(Path(__file__).resolve().parents[1])
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from validator.diagnostic import Diagnostic, Severity
from validator.lint import lint_file
from validator.rules.onboarding_state import OnboardingStateRule


BASELINE_NAME = "costformation.cz.yaml"
PROPOSAL_NAME = "costformation.proposed.cz.yaml"
STATE_RELPATH = Path(".costformation") / "gathering-state.yaml"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _error(rule_id: str, message: str, path: Path) -> Diagnostic:
    return Diagnostic(Severity.ERROR, rule_id, message, str(path))


def record_baseline(workspace: Path) -> str:
    workspace = workspace.resolve()
    baseline = workspace / BASELINE_NAME
    state_path = workspace / STATE_RELPATH
    if not baseline.exists():
        raise FileNotFoundError(baseline)
    yaml = YAML()
    state = yaml.load(state_path.read_text())
    if not isinstance(state, dict) or not isinstance(state.get("workspace"), dict):
        raise ValueError("workspace state must be a mapping")
    digest = sha256_file(baseline)
    state["workspace"]["baseline-sha256"] = digest
    with state_path.open("w") as handle:
        yaml.dump(state, handle)
    return digest


def check_workspace(workspace: Path) -> List[Diagnostic]:
    workspace = workspace.resolve()
    baseline = workspace / BASELINE_NAME
    proposal = workspace / PROPOSAL_NAME
    state_path = workspace / STATE_RELPATH
    diagnostics: List[Diagnostic] = []

    if not baseline.exists():
        return [_error("workspace-baseline-missing", f"missing {BASELINE_NAME}", baseline)]
    if not proposal.exists():
        diagnostics.append(_error("workspace-proposal-missing", f"missing {PROPOSAL_NAME}", proposal))
    if not state_path.exists():
        diagnostics.append(_error("workspace-state-missing", f"missing {STATE_RELPATH}", state_path))
        return diagnostics

    try:
        state = YAML().load(state_path.read_text())
    except (YAMLError, OSError) as exc:
        diagnostics.append(_error("workspace-state-invalid", str(exc), state_path))
        return diagnostics

    workspace_state = state.get("workspace") if isinstance(state, dict) else None
    if not isinstance(workspace_state, dict):
        diagnostics.append(_error("workspace-state-invalid", "workspace state must be a mapping", state_path))
        return diagnostics

    recorded_hash = workspace_state.get("baseline-sha256")
    current_hash = sha256_file(baseline)
    if recorded_hash != current_hash:
        diagnostics.append(_error(
            "workspace-baseline-changed",
            "baseline SHA-256 differs from the proposal's recorded baseline; rebase or replace the proposal",
            baseline,
        ))

    if proposal.exists():
        if proposal.read_bytes() == baseline.read_bytes():
            diagnostics.append(Diagnostic(
                Severity.WARN,
                "workspace-proposal-unchanged",
                "proposal is identical to baseline",
                str(proposal),
            ))
        diagnostics.extend(lint_file(str(proposal)))
    diagnostics.extend(
        OnboardingStateRule().check_integrity(workspace / "examples")
    )
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a CostFormation build workspace")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("--record-baseline", action="store_true")
    args = parser.parse_args()
    if args.record_baseline:
        try:
            record_baseline(args.workspace)
        except (FileNotFoundError, OSError, ValueError, YAMLError) as exc:
            print(exc)
            raise SystemExit(2)
    diagnostics = check_workspace(args.workspace)
    errors = sum(item.severity == Severity.ERROR for item in diagnostics)
    warnings = sum(item.severity == Severity.WARN for item in diagnostics)
    if args.format == "json":
        print(json.dumps({
            "diagnostics": [item.to_dict() for item in diagnostics],
            "summary": {"errors": errors, "warnings": warnings},
        }, indent=2))
    else:
        for item in diagnostics:
            print(item.human_readable(item.path))
        print(f"{errors} errors, {warnings} warnings")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run workspace tests and existing validator tests**

Run:

```bash
python3 -m pytest tests/test_workspace_check.py tests/test_lint_cli.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Document the command in `README.md`**

Add under “Validator and Eval”:

```markdown
# Validate the complete proposal against its recorded baseline
python3 costformation-brain/validator/workspace_check.py .
```

- [ ] **Step 7: Commit workspace validation**

```bash
git add validator/workspace_check.py tests/test_workspace_check.py tests/fixtures/workspace README.md
git commit -m "feat: validate CostFormation workspaces"
```

---

### Task 4: Add the distilled-evidence contract and validator

**Files:**

- Create: `evidence/schema.yaml`
- Create: `evidence/authority.md`
- Create: `validator/evidence_check.py`
- Create: `tests/test_evidence_check.py`
- Create: `tests/fixtures/evidence/valid.yaml`
- Create: `tests/fixtures/evidence/raw-transcript.yaml`

**Interfaces:**

- Consumes: YAML evidence documents with top-level `evidence` list.
- Produces: `validate_evidence_file(path: Path) -> list[Diagnostic]` and a CLI
  that accepts one or more evidence YAML file paths.

- [ ] **Step 1: Create evidence fixtures**

Create `tests/fixtures/evidence/valid.yaml`:

```yaml
evidence:
  - evidence_id: ev_001
    pov_id: pov_001
    source_system: customer-document
    source_record_id: architecture-plan-v2
    source_url: drive://accounts/example/architecture-plan-v2
    captured_at: 2026-07-16T14:30:00Z
    speaker: Customer platform lead
    evidence_type: customer_statement
    subject: environment_mapping
    statement: Production is represented by prod and prd.
    status: customer-confirmed
    confidence: confirmed
    customer_scope: customer-only
    promotion_status: unreviewed
```

Create `tests/fixtures/evidence/raw-transcript.yaml` with the same entry plus:

```yaml
    transcript: This complete meeting transcript must not be persisted.
```

- [ ] **Step 2: Write failing evidence tests**

Create `tests/test_evidence_check.py`:

```python
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
```

- [ ] **Step 3: Run tests and verify the module is missing**

Run:

```bash
python3 -m pytest tests/test_evidence_check.py -v
```

Expected: collection ERROR with `ModuleNotFoundError: validator.evidence_check`.

- [ ] **Step 4: Create `evidence/schema.yaml`**

```yaml
version: 1
required_fields:
  - evidence_id
  - pov_id
  - source_system
  - source_record_id
  - source_url
  - captured_at
  - speaker
  - evidence_type
  - subject
  - statement
  - status
  - confidence
  - customer_scope
  - promotion_status
statuses: [observed, customer-confirmed, inferred, conflicting, stale]
confidence_values: [confirmed, high, medium, low]
evidence_types:
  - customer_statement
  - customer_decision
  - system_observation
  - implementation_fact
  - business_context
  - agent_inference
customer_scopes: [customer-only]
promotion_statuses: [unreviewed, rejected, approved-anonymized]
prohibited_fields:
  - transcript
  - raw_transcript
  - raw_response
  - credentials
  - access_token
  - refresh_token
  - api_key
```

- [ ] **Step 5: Implement evidence validation**

Implement `validator/evidence_check.py` with:

```python
#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Any, List

from ruamel.yaml import YAML, YAMLError

REPO_ROOT = str(Path(__file__).resolve().parents[1])
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from validator.diagnostic import Diagnostic, Severity


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "evidence" / "schema.yaml"


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def validate_evidence_file(path: Path) -> List[Diagnostic]:
    yaml = YAML()
    schema = yaml.load(SCHEMA_PATH.read_text())
    try:
        data = yaml.load(path.read_text())
    except (YAMLError, OSError) as exc:
        return [Diagnostic(Severity.ERROR, "evidence-parse-error", str(exc), str(path))]
    entries = data.get("evidence") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return [Diagnostic(Severity.ERROR, "evidence-root-invalid", "'evidence' must be a list", str(path))]

    diagnostics: List[Diagnostic] = []
    prohibited = set(schema["prohibited_fields"])
    for index, entry in enumerate(entries):
        location = f"{path}:evidence[{index}]"
        if not isinstance(entry, dict):
            diagnostics.append(Diagnostic(Severity.ERROR, "evidence-entry-invalid", "entry must be a mapping", location))
            continue
        for field in schema["required_fields"]:
            if field not in entry or entry[field] in (None, ""):
                diagnostics.append(Diagnostic(Severity.ERROR, "evidence-required-field", f"missing required field '{field}'", location))
        for key in _walk_keys(entry):
            if key.lower() in prohibited:
                diagnostics.append(Diagnostic(Severity.ERROR, "evidence-prohibited-field", f"prohibited persisted field '{key}'", location))
        enum_fields = {
            "status": "statuses",
            "confidence": "confidence_values",
            "evidence_type": "evidence_types",
            "customer_scope": "customer_scopes",
            "promotion_status": "promotion_statuses",
        }
        for field, schema_field in enum_fields.items():
            if field in entry and entry[field] not in schema[schema_field]:
                diagnostics.append(Diagnostic(Severity.ERROR, "evidence-enum-invalid", f"invalid {field} '{entry[field]}'", location))
        if entry.get("status") == "inferred" and entry.get("confidence") == "confirmed":
            diagnostics.append(Diagnostic(Severity.ERROR, "evidence-inference-confirmed", "inferred evidence cannot use confirmed confidence", location))
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate distilled evidence YAML")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    diagnostics: List[Diagnostic] = []
    for path in args.files:
        diagnostics.extend(validate_evidence_file(path))
    for item in diagnostics:
        print(item.human_readable(item.path))
    errors = sum(item.severity == Severity.ERROR for item in diagnostics)
    warnings = sum(item.severity == Severity.WARN for item in diagnostics)
    print(f"{errors} errors, {warnings} warnings")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
```

The required positional `files` argument makes argparse exit 2 for CLI misuse;
the implementation exits 0 with no errors and 1 with validation errors.

- [ ] **Step 6: Write `evidence/authority.md`**

Document these normative rules:

```markdown
# Evidence Authority and Reconciliation

- CloudZero governs what is currently visible to CostFormation.
- Customer-authored documents and explicit confirmation govern business intent.
- External cloud and observability systems corroborate upstream metadata and
  usage but do not prove that CloudZero has ingested it.
- Observations, confirmations, inferences, conflicts, and stale facts remain
  distinct statuses.
- An inference never becomes confirmed without explicit human confirmation.
- Conflicts preserve both claims and are surfaced; they are never silently
  resolved by source ordering.
- Re-query stale evidence before using it to build a proposal.
- Customer evidence remains customer-only. Promotion requires separate review
  and anonymization; it is never automatic.
```

- [ ] **Step 7: Run evidence tests**

Run:

```bash
python3 -m pytest tests/test_evidence_check.py -v
```

Expected: 4 passed.

- [ ] **Step 8: Commit the evidence contract**

```bash
git add evidence validator/evidence_check.py tests/test_evidence_check.py tests/fixtures/evidence
git commit -m "feat: validate distilled evidence"
```

---

### Task 5: Add generic MCP capability discovery and policy validation

**Files:**

- Create: `connectors/capability-model.yaml`
- Create: `connectors/discovery.md`
- Create: `connectors/query-strategy.md`
- Create: `validator/capability_check.py`
- Create: `tests/test_capability_check.py`
- Create: `tests/fixtures/capabilities/valid.yaml`
- Create: `tests/fixtures/capabilities/write-auto-select.yaml`

**Interfaces:**

- Consumes: `.costformation/capabilities.yaml` with top-level `capabilities` list.
- Produces: `validate_capability_file(path: Path) -> list[Diagnostic]` and a
  generic customer-safe discovery contract consumed by agent profiles.

- [ ] **Step 1: Create capability fixtures**

Create `tests/fixtures/capabilities/valid.yaml`:

```yaml
capabilities:
  - server: example-observability
    categories: [observability, metrics, usage_volume]
    access: read-only
    status: available
    auto_select: true
```

Create `tests/fixtures/capabilities/write-auto-select.yaml`:

```yaml
capabilities:
  - server: example-cloud-control
    categories: [cloud_inventory]
    access: write-capable
    status: available
    auto_select: true
```

- [ ] **Step 2: Write failing capability tests**

Create `tests/test_capability_check.py`:

```python
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
```

- [ ] **Step 3: Run tests and verify the module is missing**

Run:

```bash
python3 -m pytest tests/test_capability_check.py -v
```

Expected: collection ERROR with
`ModuleNotFoundError: validator.capability_check`.

- [ ] **Step 4: Create the capability model**

Create `connectors/capability-model.yaml`:

```yaml
version: 1
categories:
  - cloud_inventory
  - resource_metadata
  - metrics
  - usage_volume
  - observability
  - business_context
  - meeting_context
  - crm
  - documentation
access_values: [read-only, write-capable, ambiguous]
status_values: [available, unavailable, authentication-required]
secret_fields: [credentials, password, access_token, refresh_token, api_key]
policy:
  read-only:
    auto_select_allowed: true
  write-capable:
    auto_select_allowed: false
  ambiguous:
    auto_select_allowed: false
```

- [ ] **Step 5: Implement capability validation**

Implement `validator/capability_check.py` with:

```python
#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import List

from ruamel.yaml import YAML, YAMLError

REPO_ROOT = str(Path(__file__).resolve().parents[1])
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from validator.diagnostic import Diagnostic, Severity


MODEL_PATH = Path(__file__).resolve().parents[1] / "connectors" / "capability-model.yaml"


def validate_capability_file(path: Path) -> List[Diagnostic]:
    yaml = YAML()
    model = yaml.load(MODEL_PATH.read_text())
    try:
        data = yaml.load(path.read_text())
    except (YAMLError, OSError) as exc:
        return [Diagnostic(Severity.ERROR, "capability-parse-error", str(exc), str(path))]
    entries = data.get("capabilities") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return [Diagnostic(Severity.ERROR, "capability-root-invalid", "'capabilities' must be a list", str(path))]

    diagnostics: List[Diagnostic] = []
    valid_categories = set(model["categories"])
    valid_access = set(model["access_values"])
    valid_status = set(model["status_values"])
    secret_fields = set(model["secret_fields"])
    for index, entry in enumerate(entries):
        location = f"{path}:capabilities[{index}]"
        if not isinstance(entry, dict):
            diagnostics.append(Diagnostic(Severity.ERROR, "capability-entry-invalid", "entry must be a mapping", location))
            continue
        for field in ("server", "categories", "access", "status", "auto_select"):
            if field not in entry:
                diagnostics.append(Diagnostic(Severity.ERROR, "capability-required-field", f"missing required field '{field}'", location))
        for category in entry.get("categories") or []:
            if category not in valid_categories:
                diagnostics.append(Diagnostic(Severity.ERROR, "capability-category-invalid", f"unknown category '{category}'", location))
        if entry.get("access") not in valid_access:
            diagnostics.append(Diagnostic(Severity.ERROR, "capability-access-invalid", f"invalid access '{entry.get('access')}'", location))
        if entry.get("status") not in valid_status:
            diagnostics.append(Diagnostic(Severity.ERROR, "capability-status-invalid", f"invalid status '{entry.get('status')}'", location))
        if entry.get("access") != "read-only" and entry.get("auto_select") is True:
            diagnostics.append(Diagnostic(Severity.ERROR, "capability-write-auto-select", "only read-only capabilities may be auto-selected", location))
        for key in entry:
            if str(key).lower() in secret_fields:
                diagnostics.append(Diagnostic(Severity.ERROR, "capability-secret-field", f"secret field '{key}' must not be persisted", location))
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate optional MCP capability YAML")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    diagnostics: List[Diagnostic] = []
    for path in args.files:
        diagnostics.extend(validate_capability_file(path))
    for item in diagnostics:
        print(item.human_readable(item.path))
    errors = sum(item.severity == Severity.ERROR for item in diagnostics)
    warnings = sum(item.severity == Severity.WARN for item in diagnostics)
    print(f"{errors} errors, {warnings} warnings")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
```

The required positional `files` argument makes argparse exit 2 for CLI misuse;
the implementation exits 0 with no errors and 1 with validation errors.

- [ ] **Step 6: Write generic discovery instructions**

Create `connectors/discovery.md` with this procedure:

```markdown
# Optional MCP Discovery

1. Inventory the MCP servers and tools already connected to the user's agent.
2. Read tool names, descriptions, input schemas, and declared annotations.
3. Map readable tools to categories from `capability-model.yaml` by what data
   they return, not by vendor name.
4. Mark a tool `read-only` only when its contract cannot mutate external state.
   Treat mixed or unclear contracts as `ambiguous`.
5. Set `auto_select: true` only for available read-only capabilities.
6. Persist only server name, categories, access, availability, and auto-select
   policy in `.costformation/capabilities.yaml`; never persist credentials.
7. Validate the manifest with `validator/capability_check.py`.
8. If a connector is unavailable, continue with other evidence and report the
   coverage gap.
```

Create `connectors/query-strategy.md` with a capability routing table covering:

- `cloud_inventory` and `resource_metadata` for upstream accounts, resources,
  labels, and relationships;
- `metrics`, `usage_volume`, and `observability` for allocation drivers and
  telemetry candidates;
- `business_context`, `documentation`, and `meeting_context` for customer
  intent and terminology; and
- `crm` for identity and scope when the customer has such a connector.

The document must state that CloudZero is authoritative for current
CostFormation-visible data, independent readable sources are queried in
parallel, and no write-capable tool is invoked without explicit approval.

- [ ] **Step 7: Run capability tests**

Run:

```bash
python3 -m pytest tests/test_capability_check.py -v
```

Expected: 4 passed.

- [ ] **Step 8: Commit capability discovery**

```bash
git add connectors validator/capability_check.py tests/test_capability_check.py tests/fixtures/capabilities
git commit -m "feat: define optional MCP capabilities"
```

---

### Task 6: Add the customer build profile and route it from the corpus

**Files:**

- Create: `profiles/customer.md`
- Modify: `SKILL.md`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Modify: `.cursorrules`
- Modify: `.github/copilot-instructions.md`
- Modify: `README.md`
- Modify: `tests/test_harness_instruction_consistency.py`

**Interfaces:**

- Consumes: `connectors/discovery.md`, `connectors/query-strategy.md`,
  `evidence/authority.md`, `workspace/two-file-workflow.md`.
- Produces: the customer-safe end-to-end orchestration contract used by all
  supported agents.

- [ ] **Step 1: Extend the failing instruction tests**

Add to `tests/test_harness_instruction_consistency.py`:

```python
INTERNAL_NAMES = ("Salesforce", "Granola", "Sybill")
CUSTOMER_RUNTIME_FILES = INSTRUCTION_FILES + [
    REPO_ROOT / "profiles" / "customer.md",
    REPO_ROOT / "connectors" / "discovery.md",
    REPO_ROOT / "connectors" / "query-strategy.md",
    REPO_ROOT / "README.md",
]


def test_customer_runtime_routes_to_customer_profile():
    for path in INSTRUCTION_FILES:
        assert "profiles/customer.md" in path.read_text(), path


def test_customer_runtime_excludes_internal_connector_names():
    for path in CUSTOMER_RUNTIME_FILES:
        text = path.read_text()
        for name in INTERNAL_NAMES:
            assert name not in text, f"{path}: {name}"
```

- [ ] **Step 2: Run tests and verify the profile is missing**

Run:

```bash
python3 -m pytest tests/test_harness_instruction_consistency.py -v
```

Expected: FAIL because `profiles/customer.md` does not exist and instruction
files do not route to it.

- [ ] **Step 3: Create `profiles/customer.md`**

Write these normative sections in order:

```markdown
# Customer Build Profile

## Session Initialization

1. Read `SKILL.md` and complete its startup checks.
2. Read `workspace/two-file-workflow.md`.
3. Inventory optional MCPs using `connectors/discovery.md`.
4. Validate `.costformation/capabilities.yaml` when it exists.
5. Index customer-provided files under `context/provided/` without moving or
   copying their contents into `costformation-brain/`.
6. Read distilled evidence according to `evidence/authority.md` and re-query
   anything stale.

## Build Flow

1. Query the CloudZero MCP first when creating or modifying a dimension.
2. Parse the immutable `costformation.cz.yaml` baseline.
3. Decompose the requested concept into tags, accounts, resource names,
   Kubernetes signals, existing dimensions, and relevant optional capabilities.
4. Query independent readable sources in parallel.
5. Normalize findings as observed, customer-confirmed, inferred, conflicting,
   or stale; never silently upgrade an inference.
6. Ask only for business meaning or choices the available evidence cannot
   answer.
7. Build the complete `costformation.proposed.cz.yaml`.
8. Validate with `validator/workspace_check.py` and fix all errors.
9. Present an evidence-coverage summary, concise diff, and warnings.
10. Stop. The user publishes through the CloudZero VS Code Toolkit.

## External Actions

Use available read-only tools when relevant. Never invoke a write-capable or
ambiguous external tool without explicit approval for that specific action.

## Persistence

Persist only distilled customer evidence with provenance. Never persist raw
transcripts, complete tool responses, or credentials. Never write customer
artifacts inside the `costformation-brain` repository and never promote them to
shared knowledge automatically.
```

- [ ] **Step 4: Route the profile from all instruction files**

Add this paragraph near each instruction file's CostFormation entry point:

```markdown
For the customer-safe build workflow, read
`costformation-brain/profiles/customer.md`. It routes optional MCP discovery,
evidence reconciliation, the complete proposal build, and validation.
```

Add these rows to the `SKILL.md` corpus routing table:

```markdown
| Customer build harness | `profiles/customer.md` |
| Optional MCP discovery | `connectors/discovery.md` + `connectors/query-strategy.md` |
| Evidence authority | `evidence/authority.md` |
| Baseline/proposal workflow | `workspace/two-file-workflow.md` |
```

- [ ] **Step 5: Update customer setup in `README.md`**

Add a “Build Harness” section after Quick Start that explains:

- the baseline/proposal pair;
- optional MCP capability discovery with no required vendor list;
- read-only-by-default behavior;
- distilled local evidence under the customer workspace;
- `workspace_check.py` before handoff; and
- human publishing through VS Code Toolkit.

Do not add internal connector or SE-overlay names to customer setup.

- [ ] **Step 6: Run instruction and corpus tests**

Run:

```bash
python3 -m pytest tests/test_harness_instruction_consistency.py tests/test_rules_integrity.py -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit the customer profile**

```bash
git add profiles/customer.md SKILL.md AGENTS.md CLAUDE.md .cursorrules .github/copilot-instructions.md README.md tests/test_harness_instruction_consistency.py
git commit -m "feat: add customer build profile"
```

---

### Task 7: Integrate harness checks and run full regression verification

**Files:**

- Create: `evals/harness_run.py`
- Create: `evals/harness_cases/read-only-observability.yaml`
- Create: `evals/harness_cases/ambiguous-mixed-tool.yaml`
- Create: `evals/harness_golden/read-only-observability.expected.yaml`
- Create: `evals/harness_golden/ambiguous-mixed-tool.expected.yaml`
- Create: `tests/test_harness_evals.py`
- Modify: `validator/lint.py`
- Modify: `tests/test_lint_cli.py`
- Modify: `README.md`

**Interfaces:**

- Consumes: workspace, evidence, and capability validators from Tasks 3–5.
- Produces: discoverable harness commands in `validator/lint.py --help` without
  changing existing lint behavior, plus `python3 evals/harness_run.py` for
  customer-safe behavioral golden cases.

- [ ] **Step 1: Write failing CLI help tests**

Add to `tests/test_lint_cli.py`:

```python
def test_help_lists_harness_companion_commands():
    result = run_lint("--help")
    assert result.returncode == 0
    assert "workspace_check.py" in result.stdout
    assert "evidence_check.py" in result.stdout
    assert "capability_check.py" in result.stdout
```

- [ ] **Step 2: Run the help test and verify it fails**

Run:

```bash
python3 -m pytest tests/test_lint_cli.py::test_help_lists_harness_companion_commands -v
```

Expected: FAIL because the companion commands are not mentioned.

- [ ] **Step 3: Update the lint CLI description**

Change the `argparse.ArgumentParser` description in `validator/lint.py` to:

```python
description=(
    "Validate CloudZero CostFormation YAML. Build harness companions: "
    "workspace_check.py validates baseline/proposal state, "
    "evidence_check.py validates distilled evidence, and "
    "capability_check.py validates optional MCP manifests."
)
```

Do not import the companion validators into `lint.py`; keeping the CLIs focused
prevents workspace/evidence concerns from changing existing file-lint behavior.

- [ ] **Step 4: Add representative capability-classification golden cases**

Create `evals/harness_cases/read-only-observability.yaml`:

```yaml
test_id: read-only-observability
description: Classify a read-only metrics search tool by capability, not vendor.
input:
  server: example-observability
  tool_name: search_service_metrics
  tool_description: Search service metrics and return timeseries data without changing external state.
golden_output: harness_golden/read-only-observability.expected.yaml
assertions:
  - path: capabilities.0.categories
    contains: observability
  - path: capabilities.0.categories
    contains: metrics
  - path: capabilities.0.access
    equals: read-only
  - path: capabilities.0.auto_select
    equals: true
```

Create `evals/harness_golden/read-only-observability.expected.yaml`:

```yaml
capabilities:
  - server: example-observability
    categories: [observability, metrics]
    access: read-only
    status: available
    auto_select: true
```

Create `evals/harness_cases/ambiguous-mixed-tool.yaml`:

```yaml
test_id: ambiguous-mixed-tool
description: Prevent autonomous selection when one tool can both inspect and mutate resources.
input:
  server: example-cloud-control
  tool_name: inspect_or_update_resource
  tool_description: Read resource metadata and optionally update labels when update values are supplied.
golden_output: harness_golden/ambiguous-mixed-tool.expected.yaml
assertions:
  - path: capabilities.0.categories
    contains: resource_metadata
  - path: capabilities.0.access
    equals: ambiguous
  - path: capabilities.0.auto_select
    equals: false
```

Create `evals/harness_golden/ambiguous-mixed-tool.expected.yaml`:

```yaml
capabilities:
  - server: example-cloud-control
    categories: [resource_metadata]
    access: ambiguous
    status: available
    auto_select: false
```

- [ ] **Step 5: Write the failing harness-eval integration test**

Create `tests/test_harness_evals.py`:

```python
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "evals" / "harness_run.py"


def test_harness_golden_cases_pass():
    result = subprocess.run(
        [sys.executable, str(RUNNER)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "2/2 passed" in result.stdout
```

- [ ] **Step 6: Run the harness eval test and verify the runner is missing**

Run:

```bash
python3 -m pytest tests/test_harness_evals.py -v
```

Expected: FAIL because `evals/harness_run.py` does not exist.

- [ ] **Step 7: Implement the harness golden runner**

Create `evals/harness_run.py`:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from validator.capability_check import validate_capability_file
from validator.diagnostic import Severity


CASES_DIR = REPO_ROOT / "evals" / "harness_cases"
EVALS_DIR = REPO_ROOT / "evals"


def resolve_path(value: Any, dotted_path: str) -> Any:
    current = value
    for part in dotted_path.split("."):
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def assertion_passes(data: Any, assertion: dict) -> bool:
    actual = resolve_path(data, assertion["path"])
    if "equals" in assertion:
        return actual == assertion["equals"]
    if "contains" in assertion:
        return assertion["contains"] in actual
    raise ValueError(f"unsupported assertion: {assertion}")


def main() -> None:
    yaml = YAML()
    cases = sorted(CASES_DIR.glob("*.yaml"))
    passed = 0
    for case_path in cases:
        case = yaml.load(case_path.read_text())
        golden_path = EVALS_DIR / case["golden_output"]
        golden = yaml.load(golden_path.read_text())
        diagnostics = validate_capability_file(golden_path)
        no_errors = not any(item.severity == Severity.ERROR for item in diagnostics)
        assertions_ok = all(
            assertion_passes(golden, assertion)
            for assertion in case.get("assertions") or []
        )
        ok = no_errors and assertions_ok
        print(f"{'PASS' if ok else 'FAIL'}  {case['test_id']}")
        if ok:
            passed += 1
    print(f"{passed}/{len(cases)} passed")
    raise SystemExit(0 if passed == len(cases) else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Run all focused harness tests**

Run:

```bash
python3 -m pytest tests/test_workspace_init.py tests/test_workspace_check.py tests/test_evidence_check.py tests/test_capability_check.py tests/test_harness_instruction_consistency.py tests/test_harness_evals.py tests/test_lint_cli.py -v
```

Expected: all tests pass.

- [ ] **Step 9: Run the complete repository verification suite**

Run:

```bash
python3 -m pytest tests/ -v
python3 evals/run.py --validate-golden --assert-golden
python3 evals/harness_run.py
python3 validator/lint.py --check-integrity
python3 validator/lint.py examples/patterns/*.yaml
```

Expected:

- pytest: all tests pass;
- evals: every golden case passes validation and assertions;
- integrity: no errors;
- example patterns: zero errors.

- [ ] **Step 10: Perform a customer-profile dry run in a temporary workspace**

Create a temporary workspace outside the repository and run:

```bash
python3 workspace/init.py /tmp/costformation-harness-dry-run
cp tests/fixtures/workspace/valid-baseline.yaml /tmp/costformation-harness-dry-run/costformation.cz.yaml
cp tests/fixtures/workspace/valid-proposal.yaml /tmp/costformation-harness-dry-run/costformation.proposed.cz.yaml
python3 validator/workspace_check.py /tmp/costformation-harness-dry-run --record-baseline
python3 validator/evidence_check.py tests/fixtures/evidence/valid.yaml
python3 validator/capability_check.py tests/fixtures/capabilities/valid.yaml
```

Expected: each command exits 0. Confirm manually that the temporary workspace
contains no raw transcript, complete MCP response, credential, or repository
write.

- [ ] **Step 11: Commit integration and documentation**

```bash
git add validator/lint.py evals/harness_run.py evals/harness_cases evals/harness_golden tests/test_harness_evals.py tests/test_lint_cli.py README.md
git commit -m "test: verify public build harness"
```

- [ ] **Step 12: Record the public compatibility version for the private plan**

Tag the public-core commit only after review and branch completion. Record the
exact commit SHA in the future private plan as the minimum compatible core
revision. Do not create the tag during task execution unless the repository
owner explicitly requests release tagging.

---

## Plan Completion Gate

The public-core implementation is complete only when:

- all seven task commits exist;
- the full test, eval, integrity, and example-validation commands pass;
- customer-facing runtime/setup files contain no internal connector names;
- `costformation.cz.yaml` is never edited by any workflow;
- exactly one complete `costformation.proposed.cz.yaml` is used for changes;
- capability and evidence manifests reject secrets and raw transcript fields;
- write-capable or ambiguous MCP tools cannot be auto-selected; and
- the customer-profile dry run ends without publishing or external mutation.

After this gate, initialize the private `costformation-se` repository and write
its separate implementation plan against the reviewed public commit SHA.
