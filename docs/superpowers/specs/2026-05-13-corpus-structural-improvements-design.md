# Corpus Structural Improvements

Three changes to the costformation-brain corpus to fix routing inconsistencies and reduce file fragmentation.

## Change 1: Merge conditions.md + transforms.md

**Problem:** Transforms execute before conditions evaluate — they are mechanically inseparable. An agent writing conditions must also know about transforms, and vice versa. Having them in two files means the routing table points to one when both are needed, and agents may read conditions.md without loading transforms.md first.

**Action:** Create `conditions-and-transforms.md` by combining both files. Delete `conditions.md` and `transforms.md`.

**Structure of the merged file:**

```
# Conditions & Transforms Reference

> Transforms run first, then conditions evaluate against the transformed values.
> This file is ordered by execution sequence: transforms → conditions.

## Transforms (applied first)
[current transforms.md content]

## Conditions (evaluated against transformed values)
[current conditions.md content]
```

The one-line note at the top makes the execution order self-documenting — agents reading quickly won't miss why transforms come first.

**SKILL.md routing table update:**

Remove:
```
| Writing conditions (Equals, Contains, And/Or…) | `conditions.md` |
| Applying transforms (Lower, Split, Normalize…) | `transforms.md` |
```

Replace with:
```
| Writing conditions and transforms | `conditions-and-transforms.md` |
```

## Change 2: Mark performance-rules.md as always required in routing table

**Problem:** CLAUDE.md (line 8) says "Always read `performance-rules.md` before generating any dimension definition." The SKILL.md pre-work checklist (line 31) also says this. But the routing table (line 24) presents it as task-specific alongside other optional files. An agent reading only the routing table would treat it as optional.

**Action:** Add an `← always read before any definition` annotation to the routing table entry.

**Before:**
```
| Performance rules and Snowflake cost impact | `performance-rules.md` |
```

**After:**
```
| Performance rules and Snowflake cost impact | `performance-rules.md` ← always read before any definition |
```

No changes to CLAUDE.md or the pre-work checklist — they are already correct.

## Change 3: Update telemetry routing to include sources.md

**Problem:** The routing table points telemetry tasks to `telemetry.md` only. But `sources.md` contains critical telemetry information:
- Source-to-telemetry-filter-key mappings (e.g., `CZ:Defined:ResourceSummaryDisplay` → `custom:Resource Summary Display`)
- The DimensionId vs. display Name distinction for `custom:` filter keys
- The documented typo on `NetworkSubCategory` telemetry key (`custom:Netowrking Sub-Category`) that an agent would silently "correct" and break

An agent working on telemetry without loading `sources.md` will use wrong filter keys.

**Action:** Update the routing table entry.

**Before:**
```
| Telemetry API and stream design | `telemetry.md` |
```

**After:**
```
| Telemetry API and stream design | `telemetry.md` + `sources.md` |
```

## Files Changed

| File | Change |
|---|---|
| `conditions.md` | Delete |
| `transforms.md` | Delete |
| `conditions-and-transforms.md` | Create (merged content) |
| `SKILL.md` | Update routing table: 2 rows removed (conditions, transforms), 1 row added (merged), 2 rows annotated (performance-rules, telemetry) |

## Files NOT Changed

CLAUDE.md, .cursorrules, copilot-instructions.md, AGENTS.md, performance-rules.md, telemetry.md, sources.md, allocation-design.md, examples.md, my-org/ — all remain as-is.
