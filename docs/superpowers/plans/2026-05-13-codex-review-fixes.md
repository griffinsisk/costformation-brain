# Codex Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix six findings from Codex's review — Split index contradiction, source prefix ambiguity, DefaultValue copying hazard, missing task recipe table, stale README count, and add my-org/index.yaml for context efficiency.

**Architecture:** All changes are markdown edits to corpus files and agent instruction files. No code, no config, no dependencies.

**Tech Stack:** Markdown, git

---

### Task 1: Fix Split Index and DefaultValue in dimension-types.md

**Files:**
- Modify: `dimension-types.md`

- [ ] **Step 1: Fix Split Index from 0 to 1**

Find:
```
            Index: 0    # extracts "us" from "us-east-1"
```

Replace with:
```
            Index: 1    # extracts "us" from "us-east-1"
```

- [ ] **Step 2: Add DefaultValue warning to Environment example**

Find:
```
    DefaultValue: Unknown
```
(line 13, the Environment dimension example)

Replace with:
```
    DefaultValue: Unknown    # omit unless you need a named catch-all — see performance-rules.md
```

- [ ] **Step 3: Add DefaultValue warning to Child example**

Find:
```
    DefaultValue: global
```

Replace with:
```
    DefaultValue: global    # omit unless you need a named catch-all — see performance-rules.md
```

- [ ] **Step 4: Commit**

```bash
git add dimension-types.md
git commit -m "Fix Split Index 0→1 and add DefaultValue warnings in dimension-types.md"
```

---

### Task 2: Fix source prefix rule in SKILL.md, sources.md, and examples.md

**Files:**
- Modify: `SKILL.md`
- Modify: `sources.md`
- Modify: `examples.md`

- [ ] **Step 1: Fix SKILL.md source prefix rule**

Find:
```
- Use full prefixed Source syntax: `CZ:Defined:`, `User:Defined:`, `Tag:`
```

Replace with:
```
- Use prefixed Source syntax for `CZ:Defined:`, `User:Defined:`, `Tag:`, and `K8s:` sources. Core billing sources (`Account`, `Service`, `Region`, `Resource`, `UsageFamily`, `CloudProvider`, etc.) are bare — no prefix
```

- [ ] **Step 2: Fix sources.md header and intro**

Find:
```
## Prefix Syntax — Always Required

```yaml
# CloudZero built-in dimensions:
Source: CZ:Defined:<DimensionId>

# User-defined (your own) dimensions:
Source: User:Defined:<DimensionId>

# Tag dimensions:
Source: Tag:<TagName>

# Kubernetes dimensions:
Source: K8s:Label:<LabelName>
Source: K8s:Namespace
Source: K8s:Cluster
Source: K8s:Workload
```

> Writing bare `Source: Environment` (no prefix) is **invalid** and will fail. Always use the full prefixed form.
```

Replace with:
```
## Source Syntax

Some sources require a prefix, others are bare. Use the wrong form and the definition will fail.

**Prefixed sources** — always use the full prefix:
```yaml
Source: CZ:Defined:<DimensionId>      # CloudZero built-in dimensions
Source: User:Defined:<DimensionId>    # Your own custom dimensions
Source: Tag:<TagName>                 # AWS/Azure/GCP tags
Source: K8s:Label:<LabelName>         # Kubernetes labels
Source: K8s:Namespace                 # Kubernetes namespace
Source: K8s:Cluster                   # Kubernetes cluster
Source: K8s:Workload                  # Kubernetes workload
```

**Bare sources** — no prefix, used as-is:
```yaml
Source: Account          # AWS account ID, Azure subscription, GCP project
Source: Service          # Cloud service code
Source: Region           # Cloud region
Source: Resource         # CloudZero Resource Name (CZRN)
Source: UsageFamily      # Usage family
Source: CloudProvider    # AWS, GCP, Azure, etc.
Source: UsageType        # Usage type
Source: Operation        # Cloud operation
```

> Writing `Source: CZ:Defined:Account` is **wrong** — `Account` is a bare source. Writing `Source: Environment` is also wrong — custom dimensions need `User:Defined:Environment`.
```

- [ ] **Step 3: Fix CZ:Defined:Resource in examples.md Example 6a**

Find:
```
        Sources:
          - CZ:Defined:Resource
```

Replace with:
```
        Sources:
          - Resource                    # raw CZRN — prefer CZ:Defined:ResourceSummaryDisplay for most use cases
```

- [ ] **Step 4: Commit**

```bash
git add SKILL.md sources.md examples.md
git commit -m "Fix source prefix rule: bare vs prefixed sources clarified across corpus"
```

---

### Task 3: Add DefaultValue intent comments to examples.md and file-structure.md

**Files:**
- Modify: `examples.md`
- Modify: `file-structure.md`

- [ ] **Step 1: Add comment to Department example (examples.md line 49)**

Find:
```
    DefaultValue: Unassigned
```
(the first occurrence, in the Department dimension, Example 2)

Replace with:
```
    DefaultValue: Unassigned    # intentional — top-level Explorer filter needs a named catch-all
```

- [ ] **Step 2: Add comment to Product example (examples.md line 175)**

Find:
```
    DefaultValue: Unassigned
```
(the occurrence in Example 4, Product dimension)

Replace with:
```
    DefaultValue: Unassigned    # intentional — top-level Explorer filter needs a named catch-all
```

- [ ] **Step 3: Add comment to Team example (examples.md line 237)**

Find:
```
    DefaultValue: Unassigned
```
(the occurrence in Example 5, Team dimension)

Replace with:
```
    DefaultValue: Unassigned    # intentional — top-level Explorer filter needs a named catch-all
```

- [ ] **Step 4: file-structure.md already has a warning comment — verify**

Check that `file-structure.md` line 12 contains:
```
    DefaultValue: Other                   # Omit unless you need a named bucket — defaults to "Not in Dimension"
```
If it does, no change needed. If the comment is missing, add it.

- [ ] **Step 5: Commit**

```bash
git add examples.md file-structure.md
git commit -m "Add DefaultValue intent comments to prevent blind copying"
```

---

### Task 4: Create my-org/index.yaml

**Files:**
- Create: `my-org/index.yaml`

- [ ] **Step 1: Create the file**

Write `my-org/index.yaml` with this exact content:

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

top_accounts: []       # list of strings: "<account-id> — <account-name>"
top_tags: []           # list of strings: "<tag-key> (coverage: high|medium|low)"
existing_dimensions:   # list of objects: {id: DimensionId, type: standard|allocation, name: Display Name}
  []
```

- [ ] **Step 2: Commit**

```bash
git add my-org/index.yaml
git commit -m "Create my-org/index.yaml compact summary for efficient context loading"
```

---

### Task 5: Add Common Tasks table to SKILL.md and update pre-work checklist

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: Update the pre-work checklist**

Find:
```
**Before any CostFormation work:**
1. Check if `my-org/` needs populating or refreshing (see agent instruction file for freshness rules).
2. Read all files in `my-org/` — this is the customer's org context.
3. Read `performance-rules.md` before generating any dimension definition.
4. Read `allocation-design.md` before writing any Allocation Dimension.
```

Replace with:
```
**Before any CostFormation work:**
1. Check if `my-org/` needs populating or refreshing (see agent instruction file for freshness rules).
2. Read `my-org/index.yaml` first for a compact summary, then `my-org/context.md` (always). Load full detail files as needed.
3. Read `performance-rules.md` before generating any dimension definition.
4. Read `allocation-design.md` before writing any Allocation Dimension.
```

- [ ] **Step 2: Update the routing table org context entry**

Find:
```
| Customer org context (accounts, tags, goals) | `my-org/` directory |
```

Replace with:
```
| Customer org context (accounts, tags, goals) | `my-org/index.yaml` → `my-org/` |
```

- [ ] **Step 3: Add Common Tasks table after the routing table**

Insert the following after the routing table's last row (after the `my-org/` row) and before the `**Before any CostFormation work:**` line:

```markdown

## Common Tasks

| Task | Files to read |
|---|---|
| Standard dimension (Environment, Team, Product) | `my-org/index.yaml`, `my-org/context.md`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md`, `examples.md` (3, 4, 5) |
| Allocation dimension (split shared costs) | `my-org/index.yaml`, `my-org/context.md`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md`, `allocation-design.md`, `examples.md` (7, 8, 9) |
| Telemetry allocation | `my-org/index.yaml`, `my-org/context.md`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md`, `allocation-design.md`, `telemetry.md`, `sources.md`, `examples.md` (7, 8, 9) |
| Review/debug existing dimension | `my-org/index.yaml`, `my-org/context.md`, `my-org/`, `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md` |
```

- [ ] **Step 4: Commit**

```bash
git add SKILL.md
git commit -m "Add Common Tasks recipe table and update pre-work checklist for index-first reading"
```

---

### Task 6: Update all agent instruction files (CLAUDE.md, .cursorrules, copilot-instructions.md, AGENTS.md)

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.cursorrules`
- Modify: `.github/copilot-instructions.md`
- Modify: `AGENTS.md`

All four files get the same logical changes. Do CLAUDE.md first, then replicate the non-bold-markdown content to the other three.

- [ ] **Step 1: Update CLAUDE.md top checklist (line 7)**

Find:
```
3. **Always read all files in `costformation-brain/my-org/`** before writing any definition.
```

Replace with:
```
3. **Read `costformation-brain/my-org/index.yaml` first** for a compact summary, then **`costformation-brain/my-org/context.md`** (always). Load full my-org/ detail files only when you need specifics. For new writes, load all detail files if the index is empty, stale, or missing relevant signals.
```

- [ ] **Step 2: Update CLAUDE.md pre-generation checklist (lines 25-28)**

Find:
```
- my-org/accounts.yaml — [what you found, or "empty, auto-populating"]
- my-org/tags.yaml — [what you found]
- my-org/dimensions.yaml — [what you found]
- my-org/context.md — [any business context]
```

Replace with:
```
- my-org/index.yaml — [summary: account count, dimension count, has_k8s, top signals]
- my-org/context.md — [business context found, or "empty"]
- Detail files loaded: [which ones and why, or "index was empty, loaded all"]
```

- [ ] **Step 3: Update CLAUDE.md auto-populate section (line 45-46)**

Find:
```
3. Write the results into the my-org/ files and update the `# last-synced:` header with the current ISO timestamp.
4. Compute a hash of the costformation file and write it as `# source-hash: <sha256>` in each my-org/ file.
```

Replace with:
```
3. Write the results into the my-org/ files and update the `# last-synced:` header with the current ISO timestamp.
4. Compute a hash of the costformation file and write it as `# source-hash: <sha256>` in each my-org/ file.
5. Generate/refresh `my-org/index.yaml` with counts, top signals, and a `context-hash` (sha256 of `my-org/context.md`).
```

- [ ] **Step 4: Update CLAUDE.md "Use Data" section (line 58)**

Find:
```
3. **Read `costformation-brain/my-org/`** — check for any persisted org context from prior sessions.
```

Replace with:
```
3. **Read `costformation-brain/my-org/index.yaml`** first, then **`my-org/context.md`** — check for persisted org context from prior sessions. Load detail files if the index is missing signals you need.
```

- [ ] **Step 5: Update CLAUDE.md source prefix rule**

Find the NEVER section and verify it does NOT still say "Write bare `Source: <DimensionId>` without a prefix." If present, update to:
```
- Write bare `Source: <DimensionId>` for custom or CZ dimensions without a prefix — `User:Defined:` and `CZ:Defined:` prefixes are required. Core billing sources (`Account`, `Service`, `Region`, etc.) are bare.
```

- [ ] **Step 6: Replicate changes to .cursorrules**

Apply the same logical changes to `.cursorrules` (without markdown bold formatting):
- Line 5: top checklist my-org reading rule
- Line 17: pre-generation checklist my-org section
- Lines 29-30: auto-populate step 5 for index.yaml
- Line 42: "Use Data" my-org reference
- NEVER section: source prefix rule

- [ ] **Step 7: Copy .cursorrules to the other two files**

```bash
cp .cursorrules .github/copilot-instructions.md
cp .cursorrules AGENTS.md
```

- [ ] **Step 8: Commit**

```bash
git add CLAUDE.md .cursorrules .github/copilot-instructions.md AGENTS.md
git commit -m "Update all agent instruction files: index-first reading, source prefix clarification"
```

---

### Task 7: Fix README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Fix "10 corpus files" to "9 corpus files"**

Find:
```
and a routing table that points to 10 corpus files covering syntax, conditions, transforms
```

Replace with:
```
and a routing table that points to 9 corpus files covering syntax, conditions and transforms
```

- [ ] **Step 2: Add index.yaml mention to step 4**

Find:
```
On first use, the agent automatically:
- Parses your costformation file to extract accounts, tags, dimensions, and source references
- Enriches with CloudZero MCP data if connected (account names, tag coverage, cost drivers)
- Writes the results to `my-org/` so the context persists across sessions
```

Replace with:
```
On first use, the agent automatically:
- Parses your costformation file to extract accounts, tags, dimensions, and source references
- Enriches with CloudZero MCP data if connected (account names, tag coverage, cost drivers)
- Writes the results to `my-org/` and generates a compact `my-org/index.yaml` summary so context persists and loads efficiently across sessions
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Fix README: 9 corpus files, add index.yaml mention"
```

---

### Task 8: Final verification and push

- [ ] **Step 1: Verify no stale references**

```bash
grep -rn "Index: 0" --include="*.md" . | grep -v "docs/superpowers"
grep -rn "CZ:Defined:Resource[^S]" --include="*.md" . | grep -v "docs/superpowers"
grep -rn "Prefix Syntax.*Always Required" --include="*.md" .
grep -rn "10 corpus files" --include="*.md" .
grep -rn "Read all files in.*my-org" --include="*.md" . | grep -v "docs/superpowers"
```

Expected: No matches for any of these.

- [ ] **Step 2: Verify index.yaml exists**

```bash
cat my-org/index.yaml
```

Expected: The compact summary file with schema fields.

- [ ] **Step 3: Push**

```bash
git push
```
