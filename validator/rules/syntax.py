"""Syntax rules for CostFormation YAML validation.

Rules:
    - MissingTypeRule: Every rule dict inside a dimension's Rules list must
      have a ``Type`` key.  Missing it is an ERROR.
    - UnquotedAccountIdRule: 12-digit AWS account IDs must be quoted in YAML.
      A bare 12-digit integer will be parsed as a number, which is incorrect.
    - GroupByMissingSourceRule: Every ``Type: GroupBy`` rule must declare
      ``Source`` or ``Sources`` on the rule itself.  Dimension-level source
      promotion applies to Group rules only; a bare GroupBy is an ERROR.
    - LogicalOperatorListRule: The value of ``And``/``Or``/``Not`` must be a
      YAML list of conditions.  A bare mapping is an ERROR — it may be
      rejected or silently no-op'd at publish, degrading the surrounding
      logic (e.g. an ``And`` guard quietly losing its ``Not`` clause).
"""
import re
from typing import List

from validator.diagnostic import Diagnostic, Severity
from validator.rules import Rule

# Matches a 12-digit sequence that is NOT immediately preceded or followed by
# a quote character (' or ").  Uses negative look-behind and look-ahead so
# that already-quoted values are ignored.
_UNQUOTED_ACCOUNT_RE = re.compile(r'(?<![\'"])\b(\d{12})\b(?![\'"])')


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


class GroupByMissingSourceRule(Rule):
    """ERROR groupby-missing-source — GroupBy rules must declare their own source.

    Dimension-level ``Source``/``Sources`` promotion feeds Group rule
    conditions, but a ``Type: GroupBy`` rule must carry ``Source`` or
    ``Sources`` on the rule itself.  Checks both ``Rules`` and
    ``AllocateByRules.AcrossElements.Rules``.
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        for dim_id, dim_node in dimensions.items():
            if not isinstance(dim_node, dict):
                continue

            rule_lists = [dim_node.get("Rules") or []]
            allocate = dim_node.get("AllocateByRules")
            if isinstance(allocate, dict):
                across = allocate.get("AcrossElements")
                if isinstance(across, dict):
                    rule_lists.append(across.get("Rules") or [])

            for rules in rule_lists:
                for rule in rules:
                    if not isinstance(rule, dict):
                        continue
                    if rule.get("Type") != "GroupBy":
                        continue
                    if "Source" in rule or "Sources" in rule:
                        continue

                    line = 0
                    if hasattr(rule, "lc") and rule.lc is not None:
                        line = rule.lc.line + 1

                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.ERROR,
                            rule_id="groupby-missing-source",
                            message=(
                                "GroupBy rule must declare 'Source' or 'Sources' "
                                "on the rule itself — dimension-level source "
                                "promotion applies to Group rules only"
                            ),
                            path=f"Dimensions.{dim_id}.Rules",
                            line=line,
                            dimension_id=dim_id,
                        )
                    )

        return diagnostics


_LOGICAL_OPERATORS = ("And", "Or", "Not")


class LogicalOperatorListRule(Rule):
    """ERROR logical-operator-not-list — And/Or/Not must contain a list.

    Per the CFDL reference, ``And``/``Or``/``Not`` evaluate a *list* of
    conditions.  Writing a bare mapping under the operator is invalid and can
    silently change rule semantics if the publisher drops the malformed
    clause.  Walks the entire dimension node so conditions inside Rules,
    SpendToAllocate, and AcrossElements are all covered.
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        for dim_id, dim_node in dimensions.items():
            if not isinstance(dim_node, dict):
                continue
            self._walk(dim_node, dim_id, diagnostics)

        return diagnostics

    def _walk(self, node, dim_id: str, diagnostics: List[Diagnostic]) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in _LOGICAL_OPERATORS and not isinstance(value, list):
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.ERROR,
                            rule_id="logical-operator-not-list",
                            message=(
                                f"'{key}' must contain a list of conditions "
                                f"(each item starting with '- '), not a bare "
                                f"mapping"
                            ),
                            path=f"Dimensions.{dim_id}",
                            line=self._line_of_key(node, key),
                            dimension_id=dim_id,
                        )
                    )
                self._walk(value, dim_id, diagnostics)
        elif isinstance(node, list):
            for item in node:
                self._walk(item, dim_id, diagnostics)

    @staticmethod
    def _line_of_key(node, key) -> int:
        try:
            return node.lc.data[key][0] + 1
        except (AttributeError, KeyError, TypeError, IndexError):
            return 0


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
