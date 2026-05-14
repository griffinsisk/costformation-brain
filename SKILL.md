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
| Conditions, transforms, and formatting conventions | `conditions-and-transforms.md` |
| Choosing and writing dimension types | `dimension-types.md` |
| Allocation dimension design and anti-patterns | `allocation-design.md` |
| Telemetry API and stream design | `telemetry.md` + `sources.md` |
| Performance rules and Snowflake cost impact | `performance-rules.md` ← always read before any definition |
| Real worked examples | `examples.md` |
| Finding a pattern example to start from | `examples/index.yaml` → `examples/patterns/` |
| Customer org context (accounts, tags, goals) | `my-org/index.yaml` → `my-org/` |

## Common Tasks

| Task | Files to read |
|---|---|
| Standard dimension (Environment, Team, Product) | `my-org/index.yaml`, `my-org/context.md`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md`, `examples.md` (3, 4, 5) |
| Allocation dimension (split shared costs) | `my-org/index.yaml`, `my-org/context.md`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md`, `allocation-design.md`, `examples.md` (7, 8, 9) |
| Telemetry allocation | `my-org/index.yaml`, `my-org/context.md`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md`, `allocation-design.md`, `telemetry.md`, `sources.md`, `examples.md` (7, 8, 9) |
| Review/debug existing dimension | `my-org/index.yaml`, `my-org/context.md`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md` |

**Before any CostFormation work:**
1. Check if `my-org/` needs populating or refreshing (see agent instruction file for freshness rules).
2. Read `my-org/index.yaml` first for a compact summary, then `my-org/context.md` (always). Load full detail files as needed.
3. Read `performance-rules.md` before generating any dimension definition.
4. Read `allocation-design.md` before writing any Allocation Dimension.
5. Check `examples/index.yaml` for a matching pattern before writing a dimension from scratch.

**When the user provides business context** (team mappings, CSVs, org charts, goals, constraints), persist it to `my-org/context.md` so it survives across sessions.

## Non-Negotiable Rules

ALWAYS:
- Use prefixed Source syntax for `CZ:Defined:`, `User:Defined:`, `Tag:`, and `K8s:` sources. Core billing sources (`Account`, `Service`, `Region`, `Resource`, `UsageFamily`, `CloudProvider`, etc.) are bare — no prefix
- Prefer `HasValue: false` over `DefaultValue` to avoid processing every line item (see `performance-rules.md`)
- Omit `DefaultValue` unless you specifically need a named catch-all — CostFormation defaults to "Not in Dimension" which is sufficient for most cases
- Prefer `CZ:Defined:ResourceSummaryDisplay` over `ResourceId` for resource matching
- Use `Equals`, `BeginsWith`, or `Contains` before reaching for `Matches` (regex)
- Every rule must have `Type: Group`, `Type: GroupBy`, or `Type: Metadata` — omitting Type is invalid
- Add `Lower` transforms when matching user-defined tags
- Scope `SpendToAllocate` as narrowly as possible in Allocation Dimensions
- Use a common hidden "Spend to Allocate" dimension when multiple allocation dimensions exist — prevents overlap
- Create hidden base dimensions for shared logic — reference them via `User:Defined:` instead of copy-pasting conditions
- Create dedicated telemetry target dimensions (`Hide: true`) instead of filtering streams by raw tags
- Order rules most-specific-first — first match wins

NEVER:
- Write `Source: CZ:Defined:Account` or similar — core billing sources (`Account`, `Service`, `Region`, `Resource`, etc.) are bare, not prefixed with `CZ:Defined:`
- Write bare `Source: Environment` or `Source: MyDimension` without a prefix — custom and CZ-defined dimensions require `User:Defined:` or `CZ:Defined:` prefixes
- Use raw `ResourceId` as a match source — high cardinality, expensive in Snowflake
- Layer allocation dimensions (allocation referencing another allocation's output) — causes exponential row expansion
- Create overlapping `SpendToAllocate` conditions across multiple allocation dimensions
- Send telemetry with non-UTC or non-hourly-aligned timestamps
- Reference a `User:Defined:` dimension that hasn't been published yet
- Use overly broad `Matches` (regex) patterns on high-cardinality sources
- Set `DefaultValue` unless specifically needed — CostFormation defaults to "Not in Dimension" which is sufficient. DefaultValue forces processing every line item
