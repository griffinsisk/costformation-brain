"""Syntax rules for CostFormation YAML validation.

Rules:
    - MissingTypeRule: Every rule dict inside a dimension's Rules list must
      have a ``Type`` key.  Missing it is an ERROR.
    - UnquotedAccountIdRule: 12-digit AWS account IDs must be quoted in YAML.
      A bare 12-digit integer will be parsed as a number, which is incorrect.
"""
import re
from typing import List

from validator.diagnostic import Diagnostic, Severity
from validator.rules import Rule

# Matches a 12-digit sequence that is NOT immediately preceded or followed by
# a quote character (' or ").  Uses negative look-behind and look-ahead so
# that already-quoted values are ignored.
_UNQUOTED_ACCOUNT_RE = re.compile(r'(?<![\'"])\b(\d{12})\b(?![\'"])')

# A YAML list-item dash: a "-" preceded by start-of-line or whitespace.
_BLOCK_LIST_DASH_RE = re.compile(r'(?:^|\s)-$')


def _is_yaml_value_position(line_text: str, start: int, end: int) -> bool:
    """Return True only when the 12-digit match is a bare YAML scalar *value*.

    Account IDs that appear inside a string — e.g. a ``Name: Audit (058...)``
    label or free-form prose — carry no integer-coercion risk and must not be
    flagged.  A real risk exists only when the digits are the value of a
    mapping key (``Equals: 058...``), a block list item (``- 058...``), or a
    flow-sequence element (``[058..., 058...]``).
    """
    before = line_text[:start].rstrip()
    after = line_text[end:].lstrip()

    # Whatever follows must end the value: nothing, a comment, or flow-seq syntax.
    if after and after[0] not in "#],":
        return False

    if before.endswith(":"):          # mapping value:  Equals: <id>
        return True
    if _BLOCK_LIST_DASH_RE.search(before):  # block list item:  - <id>
        return True
    if before.endswith("["):          # first flow-seq element:  [<id>, ...]
        return True
    if before.endswith(",") and "[" in before:  # later flow-seq element
        return True
    return False


class MissingTypeRule(Rule):
    """ERROR missing-type — every rule in a dimension must declare a Type."""

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        for dim_id, dim_node in dimensions.items():
            rules = dim_node.get("Rules") or []
            for rule in rules:
                if "Type" not in rule:
                    rule_name = rule.get("Name") if isinstance(rule, dict) else None
                    # ruamel CommentedMap nodes carry .lc for line/col info
                    line = 0
                    if hasattr(rule, "lc") and rule.lc is not None:
                        line = rule.lc.line + 1

                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.ERROR,
                            rule_id="missing-type",
                            message=(
                                f"Rule is missing required 'Type' field"
                                + (f" (rule: {rule_name!r})" if rule_name else "")
                            ),
                            path=f"Dimensions.{dim_id}.Rules",
                            line=line,
                            dimension_id=dim_id,
                            rule_name=rule_name,
                        )
                    )

        return diagnostics


class UnquotedAccountIdRule(Rule):
    """ERROR unquoted-account-id — 12-digit AWS account IDs must be quoted."""

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        raw_text: str = context.get("raw_text", "")

        for line_num, line_text in enumerate(raw_text.splitlines(), start=1):
            stripped = line_text.lstrip()
            # Skip pure comment lines
            if stripped.startswith("#"):
                continue

            for match in _UNQUOTED_ACCOUNT_RE.finditer(line_text):
                if not _is_yaml_value_position(line_text, match.start(), match.end()):
                    continue
                account_id = match.group(1)
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        rule_id="unquoted-account-id",
                        message=(
                            f"Account ID {account_id!r} must be quoted "
                            f"(e.g. '{account_id}') to prevent YAML integer coercion"
                        ),
                        path="",
                        line=line_num,
                        column=match.start(),
                    )
                )

        return diagnostics
