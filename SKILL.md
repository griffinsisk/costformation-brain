---
name: cloudzero-costformation
description: Use when writing, reviewing, or debugging CloudZero CostFormation YAML. Covers Custom Dimensions, Allocation Dimensions, telemetry streams, and performance rules. Trigger on any mention of CostFormation, dimensions, costformation YAML, telemetry streams, or CloudZero billing definitions.
---

# CloudZero CostFormation Skill

You are an expert CloudZero CostFormation engineer. This skill gives you everything you need to write correct, performant CostFormation YAML.

## Corpus

Consult the relevant file based on what you're working on:

| Task | File |
|---|---|
| Understanding core terminology | `concepts.md` |
| File structure and YAML skeleton | `file-structure.md` |
| Source prefixes and available sources | `sources.md` |
| Writing conditions (Match, Regex, And/Or…) | `conditions.md` |
| Applying transforms (Lowercase, Split…) | `transforms.md` |
| Choosing and writing dimension types | `dimension-types.md` |
| Allocation dimension design and anti-patterns | `allocation-design.md` |
| Telemetry API and stream design | `telemetry.md` |
| Performance rules and Snowflake cost impact | `performance-rules.md` |
| Real worked examples | `examples.md` |
| Customer org context (accounts, tags, goals) | `my-org/` directory |

Always read `performance-rules.md` before generating any dimension definition.
Always read `allocation-design.md` before writing any Allocation Dimension.
Always read all files in `my-org/` before writing any definition — this is the customer's org context.

## Non-Negotiable Rules

ALWAYS:
- Use full prefixed Source syntax: `CZ:Defined:`, `User:Defined:`, `Tag:`
- Prefer `HasValue: false` over `DefaultValue` to avoid processing every line item (see `performance-rules.md`)
- Only set `DefaultValue` when the dimension is a **top-level Explorer filter** where users expect a catch-all bucket
- Prefer `CZ:Defined:ResourceSummaryDisplay` over `ResourceId` for resource matching
- Use `Match`, `StartsWith`, or `Contains` before reaching for `Regex`
- Add `Lowercase` transforms when matching user-defined tags
- Scope `SpendToAllocate` as narrowly as possible in Allocation Dimensions
- Use a common hidden "Spend to Allocate" dimension when multiple allocation dimensions exist — prevents overlap
- Create hidden base dimensions for shared logic — reference them via `User:Defined:` instead of copy-pasting conditions
- Create dedicated telemetry target dimensions (`Hide: true`) instead of filtering streams by raw tags
- Order rules most-specific-first — first match wins

NEVER:
- Write bare `Source: <DimensionId>` without a prefix — this is invalid
- Use raw `ResourceId` as a match source — high cardinality, expensive in Snowflake
- Layer allocation dimensions (allocation referencing another allocation's output) — causes exponential row expansion
- Create overlapping `SpendToAllocate` conditions across multiple allocation dimensions
- Send telemetry with non-UTC or non-hourly-aligned timestamps
- Reference a `User:Defined:` dimension that hasn't been published yet
- Use overly broad Regex patterns on high-cardinality sources
- Set `DefaultValue` on hidden/helper dimensions — it forces processing every line item for no user benefit
