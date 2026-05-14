"""Performance rules for CostFormation YAML validation.

Rules detect allocation anti-patterns, DefaultValue misuse, unnecessary regex,
and missing Child on visible dimensions.
"""
import re
from typing import List

from validator.diagnostic import Diagnostic, Severity
from validator.rules import Rule


# Characters that indicate a genuine regex (beyond simple anchors and .* wildcard)
_REGEX_META = re.compile(r'[\\+?{}()\[\]|]')


def _is_truthy(value) -> bool:
    """Return True if a YAML value is truthy (handles bool and string 'true')."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def _line_of(node) -> int:
    """1-based line number from a ruamel node, or 0."""
    if hasattr(node, "lc") and node.lc is not None:
        return node.lc.line + 1
    return 0


def _extract_user_defined_refs(conditions) -> List[str]:
    """Walk a conditions list and return all User:Defined:<X> dimension IDs."""
    refs: List[str] = []
    if not isinstance(conditions, list):
        return refs
    for cond in conditions:
        if not isinstance(cond, dict):
            continue
        # Check And/Or wrappers recursively
        for wrapper_key in ("And", "Or"):
            inner = cond.get(wrapper_key)
            if inner:
                refs.extend(_extract_user_defined_refs(inner))
        source = cond.get("Source", "")
        if isinstance(source, str) and source.startswith("User:Defined:"):
            refs.append(source[len("User:Defined:"):])
    return refs


def _walk_conditions_for_matches(rules_list) -> list:
    """Yield (pattern, node) for every Matches condition in a Rules list."""
    results = []
    if not isinstance(rules_list, list):
        return results
    for rule in rules_list:
        if not isinstance(rule, dict):
            continue
        conditions = rule.get("Conditions") or []
        results.extend(_walk_matches_in_conditions(conditions, rule))
    return results


def _walk_matches_in_conditions(conditions, parent_node) -> list:
    """Recursively find Matches values in a conditions list."""
    results = []
    if not isinstance(conditions, list):
        return results
    for cond in conditions:
        if not isinstance(cond, dict):
            continue
        for wrapper_key in ("And", "Or"):
            inner = cond.get(wrapper_key)
            if inner:
                results.extend(_walk_matches_in_conditions(inner, cond))
        match_val = cond.get("Matches")
        if match_val is not None:
            results.append((str(match_val), cond))
    return results


class DefaultValueAllocationInputRule(Rule):
    """ERROR defaultvalue-allocation-input — hidden dim with DefaultValue that
    is referenced by an allocation dimension.

    Only fires when the hidden dim is actually used as an allocation input:
    referenced in SpendToAllocate conditions, as an AllocateByStreams filter
    target, or as a Source in an allocation dim's AcrossElements.

    Hidden dims with DefaultValue that are NOT allocation-adjacent get the
    softer defaultvalue-hidden-performance WARNING instead.
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        allocation_refs = self._collect_allocation_refs(dimensions)

        for dim_id, dim_node in dimensions.items():
            if not isinstance(dim_node, dict):
                continue
            is_hidden = _is_truthy(dim_node.get("Hide", False))
            has_default = "DefaultValue" in dim_node
            is_allocation = dim_node.get("Type") == "Allocation"

            if not (is_hidden and has_default and not is_allocation):
                continue

            if dim_id in allocation_refs:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        rule_id="defaultvalue-allocation-input",
                        message=(
                            f"Hidden dimension '{dim_id}' has DefaultValue and is "
                            f"referenced by allocation dimension(s). DefaultValue forces "
                            f"every line item through this dimension — remove it."
                        ),
                        path=f"Dimensions.{dim_id}.DefaultValue",
                        line=_line_of(dim_node),
                        dimension_id=dim_id,
                    )
                )
            else:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.WARN,
                        rule_id="defaultvalue-hidden-performance",
                        message=(
                            f"Hidden dimension '{dim_id}' has DefaultValue, which forces "
                            f"every line item through this dimension. Consider removing "
                            f"DefaultValue unless a named catch-all is intentional."
                        ),
                        path=f"Dimensions.{dim_id}.DefaultValue",
                        line=_line_of(dim_node),
                        dimension_id=dim_id,
                    )
                )
        return diagnostics

    @staticmethod
    def _collect_allocation_refs(dimensions: dict) -> set:
        """Collect all User:Defined dim IDs referenced by allocation dimensions."""
        refs = set()
        for dim_id, dim_node in dimensions.items():
            if not isinstance(dim_node, dict):
                continue
            if dim_node.get("Type") != "Allocation":
                continue
            raw = str(dim_node)
            import re
            for match in re.finditer(r'User:Defined:([A-Za-z0-9_\-]+)', raw):
                refs.add(match.group(1))
        return refs


class AllocateByStreamsSPTARule(Rule):
    """ERROR allocatebystreams-spendtoallocate — SpendToAllocate under AllocateByStreams.

    AllocateByStreams defines allocation via telemetry streams.  SpendToAllocate
    is only valid under AllocateByRules.  Having both is a configuration error.
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        for dim_id, dim_node in dimensions.items():
            if not isinstance(dim_node, dict):
                continue
            abs_node = dim_node.get("AllocateByStreams")
            if abs_node is None:
                continue
            # Check inside AllocateByStreams for SpendToAllocate
            has_spta_inside = (
                isinstance(abs_node, dict) and "SpendToAllocate" in abs_node
            )
            # Also check at the dimension level
            has_spta_top = "SpendToAllocate" in dim_node
            if has_spta_inside or has_spta_top:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        rule_id="allocatebystreams-spendtoallocate",
                        message=(
                            f"Dimension '{dim_id}' uses AllocateByStreams but also "
                            f"has SpendToAllocate. Streams-based allocation does not "
                            f"use SpendToAllocate — move it to AllocateByRules or remove it."
                        ),
                        path=f"Dimensions.{dim_id}.AllocateByStreams",
                        line=_line_of(abs_node) if hasattr(abs_node, "lc") else _line_of(dim_node),
                        dimension_id=dim_id,
                    )
                )
        return diagnostics


class LayeredAllocationRule(Rule):
    """ERROR layered-allocation — allocation dim's SpendToAllocate references another allocation.

    An allocation dimension whose SpendToAllocate conditions reference a
    User:Defined:<X> where X is itself Type: Allocation creates layered
    allocation, which is a known anti-pattern.
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        # Build set of allocation dim IDs
        alloc_dim_ids = set()
        for dim_id, dim_node in dimensions.items():
            if isinstance(dim_node, dict) and dim_node.get("Type") == "Allocation":
                alloc_dim_ids.add(dim_id)

        for dim_id, dim_node in dimensions.items():
            if not isinstance(dim_node, dict):
                continue
            if dim_node.get("Type") != "Allocation":
                continue
            # Walk SpendToAllocate conditions from AllocateByRules or top-level
            spta = None
            abr = dim_node.get("AllocateByRules")
            if isinstance(abr, dict):
                spta = abr.get("SpendToAllocate")
            if spta is None:
                spta = dim_node.get("SpendToAllocate")
            if not isinstance(spta, dict):
                continue
            conditions = spta.get("Conditions") or []
            refs = _extract_user_defined_refs(conditions)
            for ref in refs:
                if ref in alloc_dim_ids:
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.ERROR,
                            rule_id="layered-allocation",
                            message=(
                                f"Allocation dimension '{dim_id}' references another "
                                f"allocation dimension '{ref}' in SpendToAllocate. "
                                f"Layered allocation is an anti-pattern."
                            ),
                            path=f"Dimensions.{dim_id}.SpendToAllocate.Conditions",
                            line=_line_of(dim_node),
                            dimension_id=dim_id,
                        )
                    )
        return diagnostics


class DefaultValueNoIntentRule(Rule):
    """WARN defaultvalue-no-intent — DefaultValue without a comment explaining intent.

    DefaultValue forces every line item into a dimension element.  A comment
    explaining why it exists signals intentional use.
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        raw_text = context.get("raw_text", "")
        lines = raw_text.splitlines()

        for dim_id, dim_node in dimensions.items():
            if not isinstance(dim_node, dict):
                continue
            if "DefaultValue" not in dim_node:
                continue

            # Find the DefaultValue line in raw text and check for comment
            has_comment = False

            # Try to get the line number of DefaultValue from ruamel
            dv_line = 0
            if hasattr(dim_node, "lc") and dim_node.lc is not None:
                # lc.key gives (line, col) for each key in the mapping
                try:
                    dv_line = dim_node.lc.key("DefaultValue")[0] + 1  # 1-based
                except (KeyError, TypeError, AttributeError):
                    pass

            if dv_line > 0 and dv_line <= len(lines):
                line_text = lines[dv_line - 1]
                # Check same line for comment
                if "#" in line_text:
                    has_comment = True
                # Check line above for comment
                if dv_line >= 2:
                    above = lines[dv_line - 2].strip()
                    if above.startswith("#") or "#" in above:
                        has_comment = True
            else:
                # Fallback: scan raw text for DefaultValue lines
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith("DefaultValue:"):
                        if "#" in line:
                            has_comment = True
                            break
                        if i > 0 and "#" in lines[i - 1]:
                            has_comment = True
                            break

            if not has_comment:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.WARN,
                        rule_id="defaultvalue-no-intent",
                        message=(
                            f"Dimension '{dim_id}' has DefaultValue without a comment "
                            f"explaining intent. Add a comment to document why DefaultValue "
                            f"is needed."
                        ),
                        path=f"Dimensions.{dim_id}.DefaultValue",
                        line=dv_line or _line_of(dim_node),
                        dimension_id=dim_id,
                    )
                )
        return diagnostics


class BroadSpendToAllocateRule(Rule):
    """WARN broad-spendtoallocate — SpendToAllocate with a single bare condition.

    A single condition without an And wrapper in SpendToAllocate may be too broad,
    capturing more spend than intended.
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        for dim_id, dim_node in dimensions.items():
            if not isinstance(dim_node, dict):
                continue
            # Look for SpendToAllocate under AllocateByRules
            spta = None
            abr = dim_node.get("AllocateByRules")
            if isinstance(abr, dict):
                spta = abr.get("SpendToAllocate")
            if not isinstance(spta, dict):
                continue
            conditions = spta.get("Conditions")
            if not isinstance(conditions, list):
                continue
            # Single condition without And wrapper
            if len(conditions) == 1:
                cond = conditions[0]
                if isinstance(cond, dict) and "And" not in cond:
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.WARN,
                            rule_id="broad-spendtoallocate",
                            message=(
                                f"Dimension '{dim_id}' has SpendToAllocate with a single "
                                f"condition and no 'And' wrapper. This may capture more "
                                f"spend than intended."
                            ),
                            path=f"Dimensions.{dim_id}.AllocateByRules.SpendToAllocate.Conditions",
                            line=_line_of(dim_node),
                            dimension_id=dim_id,
                        )
                    )
        return diagnostics


class RegexUnnecessaryRule(Rule):
    """WARN regex-unnecessary — Matches pattern that could be a simpler operator.

    If a regex pattern contains no real metacharacters (only alphanumeric, hyphens,
    underscores, dots, ^, $, and .*), it could be replaced with Equals, BeginsWith,
    EndsWith, or Contains.
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        for dim_id, dim_node in dimensions.items():
            if not isinstance(dim_node, dict):
                continue
            rules_list = dim_node.get("Rules") or []
            matches = _walk_conditions_for_matches(rules_list)
            for pattern, cond_node in matches:
                if not _REGEX_META.search(pattern):
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.WARN,
                            rule_id="regex-unnecessary",
                            message=(
                                f"Dimension '{dim_id}': Matches pattern '{pattern}' "
                                f"contains no regex metacharacters and could be replaced "
                                f"with Equals, BeginsWith, EndsWith, or Contains."
                            ),
                            path=f"Dimensions.{dim_id}.Rules",
                            line=_line_of(cond_node),
                            dimension_id=dim_id,
                        )
                    )
        return diagnostics


class VisibleNoChildRule(Rule):
    """WARN visible-no-child — visible non-allocation dimension without Child.

    A visible dimension with Rules but no Child property likely needs one for
    proper hierarchy display. Skips hidden dims, allocation dims, and disabled dims.
    """

    def check(self, dimensions: dict, context: dict) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        for dim_id, dim_node in dimensions.items():
            if not isinstance(dim_node, dict):
                continue
            # Skip hidden
            if _is_truthy(dim_node.get("Hide", False)):
                continue
            # Skip allocation type
            if dim_node.get("Type") == "Allocation":
                continue
            # Skip disabled
            if _is_truthy(dim_node.get("Disable", False)):
                continue
            # Must have Rules
            if not dim_node.get("Rules"):
                continue
            # Must be missing Child
            if "Child" in dim_node:
                continue
            diagnostics.append(
                Diagnostic(
                    severity=Severity.WARN,
                    rule_id="visible-no-child",
                    message=(
                        f"Visible dimension '{dim_id}' has Rules but no Child property. "
                        f"Consider adding Child for proper hierarchy display."
                    ),
                    path=f"Dimensions.{dim_id}",
                    line=_line_of(dim_node),
                    dimension_id=dim_id,
                )
            )
        return diagnostics
