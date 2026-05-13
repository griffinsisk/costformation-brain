# Corpus Structural Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three routing inconsistencies in the costformation-brain corpus — merge conditions+transforms, annotate always-required files, and co-route telemetry with sources.

**Architecture:** All changes are to markdown files in the corpus root and the SKILL.md routing table. No code, no config, no dependencies.

**Tech Stack:** Markdown, git

---

### Task 1: Create merged conditions-and-transforms.md

**Files:**
- Create: `conditions-and-transforms.md`
- Read: `transforms.md` (full content)
- Read: `conditions.md` (full content)

- [ ] **Step 1: Create conditions-and-transforms.md with transforms content first, then conditions content**

Write the file with this exact structure:

```markdown
# Conditions & Transforms Reference

> Transforms run first, then conditions evaluate against the transformed values. This file is ordered by execution sequence: transforms → conditions.

## Transforms (applied first)

[paste entire content of transforms.md starting from line 3 ("Transforms mutate source values...") through end of file]

---

## Conditions (evaluated against transformed values)

[paste entire content of conditions.md starting from line 3 ("All conditions are flat...") through end of file]
```

Strip the `# Transforms Reference` and `# Conditions Reference` top-level headers from the pasted content — the merged file has its own header. Keep all subsections (## and ###) as-is.

- [ ] **Step 2: Verify the merged file**

Run: `wc -l conditions-and-transforms.md conditions.md transforms.md`

The merged file's line count should roughly equal the sum of the two source files plus ~6 lines for the new header and divider.

- [ ] **Step 3: Commit the new file (before deleting old ones)**

```bash
git add conditions-and-transforms.md
git commit -m "Create merged conditions-and-transforms.md from conditions.md + transforms.md"
```

---

### Task 2: Delete conditions.md and transforms.md

**Files:**
- Delete: `conditions.md`
- Delete: `transforms.md`

- [ ] **Step 1: Delete both files**

```bash
git rm conditions.md transforms.md
```

- [ ] **Step 2: Verify no other corpus files reference the old filenames**

```bash
grep -rn "conditions\.md\|transforms\.md" --include="*.md" . | grep -v "docs/superpowers"
```

Expected: No matches outside the specs/plans directory. If matches are found, they need updating in a follow-up step. (SKILL.md will be updated in Task 3.)

- [ ] **Step 3: Commit the deletion**

```bash
git commit -m "Delete conditions.md and transforms.md (merged into conditions-and-transforms.md)"
```

---

### Task 3: Update SKILL.md routing table

**Files:**
- Modify: `SKILL.md` (lines 19-24 of routing table)

- [ ] **Step 1: Replace the two conditions/transforms rows with one merged row**

Find:
```
| Writing conditions (Equals, Contains, And/Or…) | `conditions.md` |
| Applying transforms (Lower, Split, Normalize…) | `transforms.md` |
```

Replace with:
```
| Writing conditions and transforms | `conditions-and-transforms.md` |
```

- [ ] **Step 2: Annotate the performance-rules row**

Find:
```
| Performance rules and Snowflake cost impact | `performance-rules.md` |
```

Replace with:
```
| Performance rules and Snowflake cost impact | `performance-rules.md` ← always read before any definition |
```

- [ ] **Step 3: Update the telemetry row to include sources.md**

Find:
```
| Telemetry API and stream design | `telemetry.md` |
```

Replace with:
```
| Telemetry API and stream design | `telemetry.md` + `sources.md` |
```

- [ ] **Step 4: Verify the routing table looks correct**

```bash
grep -A 15 "| Task | File |" SKILL.md
```

Expected output — 9 rows (was 10, two removed, one added):
```
| Task | File |
|---|---|
| Understanding core terminology | `concepts.md` |
| File structure and YAML skeleton | `file-structure.md` |
| Source prefixes and available sources | `sources.md` |
| Writing conditions and transforms | `conditions-and-transforms.md` |
| Choosing and writing dimension types | `dimension-types.md` |
| Allocation dimension design and anti-patterns | `allocation-design.md` |
| Telemetry API and stream design | `telemetry.md` + `sources.md` |
| Performance rules and Snowflake cost impact | `performance-rules.md` ← always read before any definition |
| Real worked examples | `examples.md` |
| Customer org context (accounts, tags, goals) | `my-org/` directory |
```

- [ ] **Step 5: Commit**

```bash
git add SKILL.md
git commit -m "Update SKILL.md routing table: merge conditions+transforms, annotate perf-rules and telemetry"
```

---

### Task 4: Final verification and push

- [ ] **Step 1: Verify old files are gone, new file exists**

```bash
ls -la conditions.md transforms.md conditions-and-transforms.md 2>&1
```

Expected: `conditions.md` and `transforms.md` not found, `conditions-and-transforms.md` exists.

- [ ] **Step 2: Verify no dangling references**

```bash
grep -rn "conditions\.md\|transforms\.md" --include="*.md" . | grep -v "docs/superpowers"
```

Expected: No matches.

- [ ] **Step 3: Push**

```bash
git push
```
