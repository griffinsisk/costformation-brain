"""Integrity rules for the CostFormation example library.

These rules operate on the filesystem (examples/ directory) rather than a parsed
dimension dict. Each class exposes `check_integrity(examples_dir) -> List[Diagnostic]`
in addition to the standard `check()` stub required by the Rule ABC.
"""
import pathlib
import re
from typing import List

from ruamel.yaml import YAML

from validator.diagnostic import Diagnostic, Severity
from validator.rules import Rule

# Customer names that must not appear in public example files (case-insensitive).
# 'cloudzero' is intentionally excluded — it is the product name and appears legitimately.
CUSTOMER_BLOCKLIST = ["coinbase", "coderabbit", "draftkings", "expedia", "nubank"]

# All 8 required fields for every index entry.
REQUIRED_METADATA_FIELDS = [
    "id",
    "file",
    "complexity",
    "tags",
    "use_when",
    "prerequisites",
    "teaches",
    "anti_patterns",
]


class IndexConsistencyRule(Rule):
    """Verify that index.yaml and examples/patterns/ are in sync.

    Raises:
        index-missing-file   — an index entry's file: path does not exist on disk
        index-unindexed-pattern — a *.yaml in examples/patterns/ has no index entry
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        return []

    def check_integrity(self, examples_dir: pathlib.Path) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        index_path = examples_dir / "index.yaml"
        if not index_path.exists():
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    rule_id="index-missing-file",
                    message=f"index.yaml not found at {index_path}",
                    path=str(index_path),
                )
            )
            return diagnostics

        with index_path.open() as fh:
            index_data = YAML().load(fh)

        patterns_dir = examples_dir / "patterns"
        entries = index_data.get("patterns", []) if index_data else []

        # Collect file paths referenced in the index.
        indexed_files: set[str] = set()
        for entry in entries:
            file_ref = entry.get("file", "")
            indexed_files.add(file_ref)
            target = examples_dir / file_ref
            if not target.exists():
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        rule_id="index-missing-file",
                        message=(
                            f"Index entry '{entry.get('id', '?')}' references "
                            f"'{file_ref}' which was not found on disk"
                        ),
                        path=str(target),
                    )
                )

        # Check that every pattern file on disk appears in the index.
        if patterns_dir.exists():
            for yaml_file in sorted(patterns_dir.glob("*.yaml")):
                relative = yaml_file.relative_to(examples_dir).as_posix()
                if relative not in indexed_files:
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.ERROR,
                            rule_id="index-unindexed-pattern",
                            message=(
                                f"Pattern file '{relative}' exists on disk "
                                f"but has no entry in index.yaml"
                            ),
                            path=str(yaml_file),
                        )
                    )

        return diagnostics


class MetadataIncompleteRule(Rule):
    """Verify that every index entry contains all 8 required metadata fields.

    Raises:
        metadata-incomplete — one or more required fields are absent or empty
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        return []

    def check_integrity(self, examples_dir: pathlib.Path) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        index_path = examples_dir / "index.yaml"
        if not index_path.exists():
            return diagnostics

        with index_path.open() as fh:
            index_data = YAML().load(fh)

        entries = index_data.get("patterns", []) if index_data else []

        for entry in entries:
            entry_id = entry.get("id", "<unknown>")
            missing = [
                field
                for field in REQUIRED_METADATA_FIELDS
                if field not in entry or entry[field] is None or entry[field] == ""
            ]
            if missing:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.WARN,
                        rule_id="metadata-incomplete",
                        message=(
                            f"Index entry '{entry_id}' is missing required "
                            f"fields: {', '.join(missing)}"
                        ),
                        path=str(index_path),
                    )
                )

        return diagnostics


class CustomerDataLeakRule(Rule):
    """Scan examples/patterns/ for customer-identifying data.

    Detects:
    - Blocked customer names (case-insensitive) in non-comment lines
    - 'reference/' path strings in non-comment content
    - Real 12-digit AWS account IDs extracted from reference/customer-examples/
      (only when that directory exists and is non-empty)

    All findings are Severity.ERROR with rule_id 'customer-data-leak'.
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        return []

    def _extract_real_account_ids(self, reference_dir: pathlib.Path) -> set[str]:
        """Return all 12-digit numbers found quoted in customer example files."""
        account_ids: set[str] = set()
        if not reference_dir.exists():
            return account_ids
        for yaml_file in reference_dir.glob("*.yaml"):
            try:
                text = yaml_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            # Match quoted 12-digit sequences (both ' and ").
            for match in re.finditer(r"""['"](\d{12})['"]""", text):
                account_ids.add(match.group(1))
        return account_ids

    def _non_comment_lines(self, text: str) -> List[tuple[int, str]]:
        """Return (line_number, line_text) for lines that are not pure YAML comments."""
        result = []
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.lstrip()
            if not stripped.startswith("#"):
                result.append((i, line))
        return result

    def check_integrity(self, examples_dir: pathlib.Path) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        patterns_dir = examples_dir / "patterns"
        if not patterns_dir.exists():
            return diagnostics

        # Derive reference/customer-examples relative to examples_dir.
        reference_dir = examples_dir.parent / "reference" / "customer-examples"
        real_account_ids = self._extract_real_account_ids(reference_dir)

        blocklist_pattern = re.compile(
            r"\b(" + "|".join(re.escape(name) for name in CUSTOMER_BLOCKLIST) + r")\b",
            re.IGNORECASE,
        )
        # Pattern for reference/ path strings (non-comment content only).
        reference_path_pattern = re.compile(r"reference/", re.IGNORECASE)

        for yaml_file in sorted(patterns_dir.glob("*.yaml")):
            try:
                text = yaml_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            for lineno, line in self._non_comment_lines(text):
                # Check for blocked customer names.
                match = blocklist_pattern.search(line)
                if match:
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.ERROR,
                            rule_id="customer-data-leak",
                            message=(
                                f"Blocked customer name '{match.group(1)}' found in "
                                f"{yaml_file.name}:{lineno}"
                            ),
                            path=str(yaml_file),
                            line=lineno,
                        )
                    )

                # Check for reference/ path strings.
                if reference_path_pattern.search(line):
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.ERROR,
                            rule_id="customer-data-leak",
                            message=(
                                f"Internal 'reference/' path found in "
                                f"{yaml_file.name}:{lineno}"
                            ),
                            path=str(yaml_file),
                            line=lineno,
                        )
                    )

                # Check for real customer account IDs.
                for account_id in real_account_ids:
                    # Only match quoted occurrences to avoid false positives on
                    # partial matches inside longer numbers.
                    if re.search(r"""['"]""" + re.escape(account_id) + r"""['"]""", line):
                        diagnostics.append(
                            Diagnostic(
                                severity=Severity.ERROR,
                                rule_id="customer-data-leak",
                                message=(
                                    f"Real customer account ID '{account_id}' found in "
                                    f"{yaml_file.name}:{lineno}"
                                ),
                                path=str(yaml_file),
                                line=lineno,
                            )
                        )

        return diagnostics
