# Codex Review Fixes

Six fixes plus one addition addressing findings from Codex's structural review of costformation-brain.

## Fix 1 (P1): Split Index contradiction in dimension-types.md

**Problem:** `dimension-types.md:48` shows `Index: 0`. The official CFDL docs and `conditions-and-transforms.md` both say Split index is 1-based. Agents will copy the example.

**Action:** Change `Index: 0` to `Index: 1` in the Child dimension example. The comment "extracts 'us' from 'us-east-1'" remains correct — `Index: 1` extracts the first segment.

## Fix 2 (P1): CZ:Defined:Resource ambiguity + source prefix rule

**Problem:** `examples.md:285` uses `CZ:Defined:Resource` which doesn't appear in the official CFDL source list. The correct source ID for CZRN is bare `Resource`. Additionally, `SKILL.md:38` says "Use full prefixed Source syntax" as if every source needs a prefix — this contradicts valid bare core sources like `Account`, `Service`, `Region`, and `Resource`. And `sources.md:3` says "Prefix Syntax — Always Required" with `sources.md:22` reinforcing "always use the full prefixed form."

**Action (examples.md):** Change `CZ:Defined:Resource` to `Resource` in Example 6a. Add a YAML comment noting this is the raw CZRN and to prefer `CZ:Defined:ResourceSummaryDisplay` for most use cases.

**Action (SKILL.md):** Update the prefixed source rule from:
```
Use full prefixed Source syntax: `CZ:Defined:`, `User:Defined:`, `Tag:`
```
To:
```
Use prefixed Source syntax for CZ:Defined:, User:Defined:, Tag:, and K8s: sources. Core billing sources (Account, Service, Region, Resource, UsageFamily, CloudProvider, etc.) are bare — no prefix.
```

**Action (sources.md):** Update the section header from "Prefix Syntax — Always Required" to "Source Syntax." Update the body text to clarify that core billing and CZRN sources (`Account`, `Service`, `Region`, `Resource`, `UsageFamily`, `CloudProvider`, etc.) are bare — no prefix needed. Only `CZ:Defined:`, `User:Defined:`, `Tag:`, and `K8s:` sources use prefixes. Remove or reword the "always use the full prefixed form" statement to reflect this distinction.

## Fix 3 (P2): DefaultValue copying hazard

**Problem:** DefaultValue appears in examples and skeletons without context. Agents copy the pattern blindly, contradicting the "omit unless needed" guidance in SKILL.md.

**Locations to fix:**
- `examples.md:49` — `DefaultValue: Unassigned` in Department dimension
- `examples.md:175` — `DefaultValue: Unassigned` in Product dimension
- `examples.md:237` — `DefaultValue: Unassigned` in Team dimension
- `file-structure.md` — `DefaultValue: Other` in the generic skeleton
- `dimension-types.md` — `DefaultValue: Unknown` in the Environment example and `DefaultValue: global` in the Child example

**Action:** Add inline YAML comment `# intentional — this is a top-level Explorer filter` to each examples.md instance. For the generic skeletons in file-structure.md and dimension-types.md, either remove DefaultValue or add a comment: `# omit unless you need a named catch-all — see performance-rules.md`.

## Fix 4 (P2): Task recipe table in SKILL.md

**Problem:** For "add Team dimension," the agent must infer which files to load. A task recipe table reduces misses.

**Action:** Add a "Common Tasks" section after the routing table in SKILL.md:

```markdown
## Common Tasks

| Task | Files to read |
|---|---|
| Standard dimension (Environment, Team, Product) | `my-org/index.yaml`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md`, `examples.md` (3, 4, 5) |
| Allocation dimension (split shared costs) | `my-org/index.yaml`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md`, `allocation-design.md`, `examples.md` (7, 8, 9) |
| Telemetry allocation | `my-org/index.yaml`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md`, `allocation-design.md`, `telemetry.md`, `sources.md`, `examples.md` (7, 8, 9) |
| Review/debug existing dimension | `my-org/index.yaml`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md` |
```

Every row is fully explicit — no "All of the above." Review/debug includes `sources.md` and `dimension-types.md` because many debug failures are invalid source syntax or missing rule types.

## Fix 5 (P3): Stale "10 corpus files" in README.md

**Problem:** README.md:80 says "10 corpus files" — now 9 after the conditions+transforms merge.

**Action:** Change "10 corpus files" to "9 corpus files."

## Fix 6: my-org/index.yaml

**Problem:** Once a real customer populates my-org/, "always read all files" becomes the largest context load. Agents need a compact summary to read first.

**Action:** Create `my-org/index.yaml` with this structure:

```yaml
# Compact summary of org context. Read this first.
# Load full my-org/ files only when you need detail for the requested dimension.
# For new writes: load all detail files if this index is empty, stale, or missing relevant signals.
#
# last-synced: never
# source-hash: none
# context-hash: none

account_count: 0
dimension_count: 0
has_k8s: false

top_accounts: []       # list of strings: "account-id — account-name"
top_tags: []           # list of strings: "tag-key (coverage: high|medium|low)"
existing_dimensions:   # list of objects
  # - id: DimensionId
  #   type: standard|allocation
  #   name: Display Name
```

Schema notes:
- `top_accounts`: list of strings, format `"<account-id> — <account-name>"`
- `top_tags`: list of strings, format `"<tag-key> (coverage: high|medium|low)"`
- `existing_dimensions`: list of objects with `id` (string, the YAML key), `type` (string, `standard` or `allocation`), `name` (string, display name)
- `context-hash`: sha256 of `context.md` at time of index generation. Agents compare against current `context.md` hash — if they differ, re-read `context.md` and refresh the index.

**context.md is always read** because it's small and business-critical. The `context-hash` in the index lets agents detect when it was updated outside the auto-populate flow (e.g., user edited directly) and refresh the index accordingly.

**Action (CLAUDE.md + equivalents):** Update EVERY occurrence of my-org/ reading rules across ALL sections — top checklist, pre-generation checklist, auto-populate section, and "Use Data Before Asking Questions." Specifically:

Top checklist — change from:
```
Always read all files in costformation-brain/my-org/ before writing any definition.
```
To:
```
Read costformation-brain/my-org/index.yaml first for a compact summary, then costformation-brain/my-org/context.md (always). Load full my-org/ detail files only when you need specifics for the requested dimension. For new writes, load all detail files if the index is empty, stale, or missing relevant signals.
```

Pre-generation checklist — update the my-org section to reference index.yaml first, then context.md, then detail files as needed.

Auto-populate section — update to generate/refresh `index.yaml` (including `context-hash`) when populating my-org/.

"Use Data Before Asking Questions" step 3 — update to reference index.yaml first.

**Action (SKILL.md):** Update the pre-work checklist (lines 29-30) from:
```
Read all files in my-org/ — this is the customer's org context.
```
To:
```
Read my-org/index.yaml first, then my-org/context.md (always). Load full detail files as needed.
```

Update the routing table entry for org context:
```
| Customer org context (accounts, tags, goals) | `my-org/index.yaml` → `my-org/` |
```

**Action (README.md):** Add `my-org/index.yaml` to the step 4 description so agents and users discover it naturally.

## Files Changed

| File | Changes |
|---|---|
| `dimension-types.md` | Fix Split Index: 0 → 1. Add DefaultValue warning comments. |
| `examples.md` | Fix CZ:Defined:Resource → Resource. Add DefaultValue intent comments. |
| `file-structure.md` | Add DefaultValue warning comment to skeleton. |
| `sources.md` | Update prefix section header and body to clarify bare vs prefixed sources. |
| `SKILL.md` | Fix source prefix rule. Add Common Tasks table. Update my-org routing and pre-work checklist. |
| `README.md` | Fix "10 corpus files" → "9 corpus files." Add index.yaml mention. |
| `CLAUDE.md` | Update ALL my-org/ references (top checklist, pre-gen checklist, auto-populate, Use Data). Update auto-populate to generate index. |
| `.cursorrules` | Same my-org/ and source prefix changes as CLAUDE.md equivalent sections. |
| `.github/copilot-instructions.md` | Same changes as .cursorrules. |
| `AGENTS.md` | Same changes as .cursorrules. |
| `my-org/index.yaml` | Create new file with typed schema. |

## Files NOT Changed

`conditions-and-transforms.md`, `performance-rules.md`, `allocation-design.md`, `telemetry.md`, `my-org/accounts.yaml`, `my-org/tags.yaml`, `my-org/dimensions.yaml`, `my-org/context.md` — all remain as-is.
