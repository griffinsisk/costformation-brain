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
INTERNAL_NAMES = ("Salesforce", "Granola", "Sybill")
CUSTOMER_RUNTIME_FILES = INSTRUCTION_FILES + [
    REPO_ROOT / "profiles" / "customer.md",
    REPO_ROOT / "connectors" / "discovery.md",
    REPO_ROOT / "connectors" / "query-strategy.md",
    REPO_ROOT / "README.md",
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


def test_customer_runtime_routes_to_customer_profile():
    for path in INSTRUCTION_FILES:
        assert "profiles/customer.md" in path.read_text(), path


def test_customer_runtime_excludes_internal_connector_names():
    for path in CUSTOMER_RUNTIME_FILES:
        text = path.read_text()
        for name in INTERNAL_NAMES:
            assert name not in text, f"{path}: {name}"
