"""Source rules for CostFormation YAML validation.

Rules:
    - SourcePrefixRule: Validates that source references use correct prefixes.
    - UnresolvedUserDefinedRule: Ensures all User:Defined:<X> refs resolve to
      a dimension defined in the same file.

Helper:
    - extract_all_sources: Walks a dimension definition recursively to find
      every source reference string.
"""
from typing import List, Tuple

from validator.diagnostic import Diagnostic, Severity
from validator.rules import CORE_BILLING_SOURCES, VALID_PREFIXES, Rule


def _line_of(node) -> int:
    """Return 1-based line number from a ruamel.yaml node, or 0."""
    if hasattr(node, "lc") and node.lc is not None:
        return node.lc.line + 1
    return 0


def _collect_sources_from_value(source_val, line: int, yaml_path: str, dim_id: str,
                                out: List[Tuple[str, int, str, str]]):
    """Append (source_string, line, yaml_path, dim_id) for a Source value.

    source_val can be a string or a list of strings (array notation).
    """
    if isinstance(source_val, str):
        out.append((source_val, line, yaml_path, dim_id))
    elif isinstance(source_val, list):
        for item in source_val:
            if isinstance(item, str):
                item_line = _line_of(item) if hasattr(item, "lc") else line
                out.append((item, item_line, yaml_path, dim_id))


def _walk_conditions(conditions, dim_id: str, base_path: str,
                     out: List[Tuple[str, int, str, str]]):
    """Recursively extract source references from a conditions list.

    Handles And/Or/Not nesting.
    """
    if not isinstance(conditions, list):
        return
    for i, cond in enumerate(conditions):
        if not isinstance(cond, dict):
            continue
        cond_path = f"{base_path}.Conditions[{i}]"

        # Direct Source on condition
        if "Source" in cond:
            src = cond["Source"]
            line = _line_of(cond)
            _collect_sources_from_value(src, line, cond_path, dim_id, out)

        # And / Or contain lists of nested conditions
        for logical_key in ("And", "Or"):
            if logical_key in cond:
                nested = cond[logical_key]
                _walk_conditions(nested, dim_id, f"{cond_path}.{logical_key}", out)

        # Not contains a single condition dict (wrap in list for recursion)
        if "Not" in cond:
            not_val = cond["Not"]
            if isinstance(not_val, dict):
                _walk_conditions([not_val], dim_id, f"{cond_path}.Not", out)
            elif isinstance(not_val, list):
                _walk_conditions(not_val, dim_id, f"{cond_path}.Not", out)


def extract_all_sources(dim_id: str, dim_def) -> List[Tuple[str, int, str, str]]:
    """Extract all source references from a dimension definition.

    Returns a list of (source_string, line, yaml_path, dim_id).
    """
    out: List[Tuple[str, int, str, str]] = []
    base = f"Dimensions.{dim_id}"

    # Dimension-level Source / Sources
    if "Source" in dim_def:
        line = _line_of(dim_def)
        _collect_sources_from_value(dim_def["Source"], line, f"{base}.Source", dim_id, out)
    if "Sources" in dim_def:
        sources_node = dim_def["Sources"]
        line = _line_of(sources_node) if hasattr(sources_node, "lc") else _line_of(dim_def)
        if isinstance(sources_node, list):
            for item in sources_node:
                if isinstance(item, str):
                    item_line = _line_of(item) if hasattr(item, "lc") else line
                    out.append((item, item_line, f"{base}.Sources", dim_id))

    # Walk each rule
    rules = dim_def.get("Rules") or []
    for r_idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            continue
        rule_path = f"{base}.Rules[{r_idx}]"

        # Rule-level Source / Sources
        if "Source" in rule:
            line = _line_of(rule)
            _collect_sources_from_value(rule["Source"], line, f"{rule_path}.Source", dim_id, out)
        if "Sources" in rule:
            sources_node = rule["Sources"]
            line = _line_of(sources_node) if hasattr(sources_node, "lc") else _line_of(rule)
            if isinstance(sources_node, list):
                for item in sources_node:
                    if isinstance(item, str):
                        item_line = _line_of(item) if hasattr(item, "lc") else line
                        out.append((item, item_line, f"{rule_path}.Sources", dim_id))

        # Conditions within each rule
        conditions = rule.get("Conditions") or []
        _walk_conditions(conditions, dim_id, rule_path, out)

    return out


class SourcePrefixRule(Rule):
    """Validates source prefix usage.

    Emits:
        source-prefix-missing — source not in CORE_BILLING_SOURCES and no valid prefix
        source-prefix-wrong — CZ:Defined: prefix on a core billing source
        source-resourceid — bare ResourceId should be CZ:Defined:ResourceSummaryDisplay
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []

        for dim_id, dim_def in dimensions.items():
            for src, line, path, d_id in extract_all_sources(dim_id, dim_def):
                # Check: bare ResourceId
                if src == "ResourceId":
                    diagnostics.append(Diagnostic(
                        severity=Severity.ERROR,
                        rule_id="source-resourceid",
                        message=(
                            "Source 'ResourceId' is not valid. "
                            "Use 'CZ:Defined:ResourceSummaryDisplay' instead."
                        ),
                        path=path,
                        line=line,
                        dimension_id=d_id,
                    ))
                    continue

                # Check: CZ:Defined: prefix on a core billing source
                if src.startswith("CZ:Defined:"):
                    bare_name = src[len("CZ:Defined:"):]
                    if bare_name in CORE_BILLING_SOURCES:
                        diagnostics.append(Diagnostic(
                            severity=Severity.ERROR,
                            rule_id="source-prefix-wrong",
                            message=(
                                f"Source '{src}' uses CZ:Defined: prefix on core "
                                f"billing source '{bare_name}'. Use bare '{bare_name}' instead."
                            ),
                            path=path,
                            line=line,
                            dimension_id=d_id,
                        ))
                    continue

                # If it has a valid prefix or is a core billing source, it's fine
                if src in CORE_BILLING_SOURCES:
                    continue
                if any(src.startswith(p) for p in VALID_PREFIXES):
                    continue

                # No valid prefix and not a core billing source
                diagnostics.append(Diagnostic(
                    severity=Severity.ERROR,
                    rule_id="source-prefix-missing",
                    message=(
                        f"Source '{src}' is not a core billing source and has no "
                        f"valid prefix. Did you mean 'User:Defined:{src}'?"
                    ),
                    path=path,
                    line=line,
                    dimension_id=d_id,
                ))

        return diagnostics


class UnresolvedUserDefinedRule(Rule):
    """Checks that all User:Defined:<X> references resolve to defined dimensions.

    Skipped when context['standalone'] is True.
    """

    _PREFIX = "User:Defined:"

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        if context.get("standalone"):
            return []

        diagnostics: List[Diagnostic] = []
        defined_ids = set(dimensions.keys())

        # Collect all User:Defined refs from sources AND Child fields
        all_refs: List[Tuple[str, int, str, str]] = []
        for dim_id, dim_def in dimensions.items():
            all_refs.extend(extract_all_sources(dim_id, dim_def))
            # Child is also a dimension reference
            child = dim_def.get("Child")
            if isinstance(child, str) and child.startswith(self._PREFIX):
                line = _line_of(dim_def)
                all_refs.append((child, line, f"Dimensions.{dim_id}.Child", dim_id))

        for src, line, path, dim_id in all_refs:
            if not isinstance(src, str) or not src.startswith(self._PREFIX):
                continue
            ref_name = src[len(self._PREFIX):]
            if ref_name not in defined_ids:
                diagnostics.append(Diagnostic(
                    severity=Severity.ERROR,
                    rule_id="unresolved-user-defined",
                    message=(
                        f"Source '{ref_name}' (referenced as '{src}') "
                        f"is not defined in this file."
                    ),
                    path=path,
                    line=line,
                    dimension_id=dim_id,
                ))

        return diagnostics
