# Onboarding Journey — Orchestrator

This document is an **instruction document for agents**. Follow it the same way you follow SKILL.md: imperatively, rule-first. The audience is an AI agent orchestrating the journey; a technical customer may read along.

---

## 1. What This Is

A guided, resumable path from a near-empty costformation file to allocated dimensions and (optionally) unit cost. Five phases, ordered but skippable. Skips are recorded in the state file with a reason so they can be revisited.

| # | Phase | Phase doc | One-line summary |
|---|---|---|---|
| 1 | `discover` | `onboarding/phase-1-discover.md` | Inventory every billing signal across all six sources; confirm interpretations |
| 2 | `dimensions` | `onboarding/phase-2-dimensions.md` | Cross-reference signals against the candidate catalog; build a ranked starter set |
| 3 | `shared-spend` | `onboarding/phase-3-shared-spend.md` | Build the cross-dimension shared-spend matrix; classify each bucket |
| 4 | `allocation` | `onboarding/phase-4-allocation.md` | Walk each unallocated bucket up the split-method ladder, per dimension (loop) |
| 5 | `unit-cost` | `onboarding/phase-5-unit-cost.md` | Optional: pick a unit, design demand-side telemetry, produce unit cost view |

Phases 1–2 run once globally. Phases 3–4 run as a per-dimension loop driven by the shared-spend matrix. Phase 5 is optional; skipping it is a first-class exit.

**Do not skip recording.** Every phase transition, skip reason, and exit-check result is written to `my-org/onboarding-state.yaml` before the status flips. A loosely-following agent leaves visible gaps; `lint.py --check-integrity` surfaces them.

---

## 2. Entry Rules

Four rules. Each is independent; read all four.

### 2.1 Auto-Offer Once

**Trigger:** during the agent's existing startup my-org freshness checks, if **both** conditions hold:
1. The costformation file has fewer than 3 custom dimensions.
2. `my-org/onboarding-state.yaml` does not exist, or exists but has neither `journey.offered` nor `journey.declined: true`.

**Action:** offer the journey once. Record `journey.offered: <ISO date today>` in the state file. If the customer declines, set `journey.declined: true`. Never re-offer.

```
"You have 1 custom dimension. Want me to walk you through building out a complete
allocation model? (This takes several sessions; you can pause and resume.)"
```

A decline is final for this org. Do not re-raise the auto-offer on subsequent sessions.

### 2.2 Explicit Always

The following phrases (exact or close paraphrase) always enter or resume the journey, at any phase:

- "onboard"
- "suggest dimensions"
- "continue onboarding"
- "where were we"

On these phrases: read the state file (or initialize it if absent), identify the current phase, and proceed from there. The auto-offer condition is irrelevant — explicit entry bypasses it.

### 2.3 Session-Start Wait Check (Independent of Auto-Offer)

**On every session start**, regardless of dimension count or offer history, scan `my-org/onboarding-state.yaml` for any entry (phase-level or `per-dimension`) whose `status` is `waiting-external` and whose `verify-after` date is in the past relative to today.

If found, surface once per session:

```
"Telemetry verification for stream 'tenant-usage' is overdue (verify-after: 2026-06-14).
Check it now?"
```

**This check must NOT be gated on the auto-offer condition.** A customer mid-journey already has 3+ custom dimensions and was already offered, so the auto-offer check (`< 3 dimensions AND no prior offer`) is structurally unreachable for them. Gating the wait check on the auto-offer would permanently suppress it for the customers who need it most — those who deployed a collector and then continued building out dimensions.

Surface the wait check unconditionally. The customer can dismiss it; it does not recur within the same session. "Once per session" means: don't repeat the nudge within the same conversation — conversational context is sufficient tracking; nothing is persisted to the state file for this purpose, and a new session will re-surface any overdue wait until it is resolved.

### 2.4 Resume Reconciliation

On every journey entry or resume (explicit phrase or continuing an in-progress phase), run:

1. **Source-hash freshness check** — compare the costformation file's current sha256 against the `# source-hash:` header in `my-org/` detail files. If they differ, the file changed outside the journey; re-populate my-org/ before proceeding.
2. **MCP dimension-list diff** — list dimensions currently published in CloudZero (via MCP) and compare against what the state file shows as complete. If the customer published dimensions outside the journey, update the state and matrix to reflect reality.

**Update state and the shared-spend matrix first. Then act.**

**The state file is a cache of journey position, not ground truth.** Never trust a recorded status over observed state (MCP + filesystem).

---

## 3. State File Schema

**Location:** `my-org/onboarding-state.yaml`

The agent creates this file on first journey entry. It updates the file at every phase transition. After every write, run:

```bash
python3 costformation-brain/validator/lint.py --check-integrity
```

Fix all ERRORs immediately. WARNINGs on missing artifacts are acceptable if the artifact hasn't been created yet in the session.

### 3.1 Valid Values

| Field | Valid values |
|---|---|
| Phase names | `discover`, `dimensions`, `shared-spend`, `allocation`, `unit-cost` |
| Status | `not_started`, `in_progress`, `complete`, `skipped`, `waiting-external` |
| `complete` requires | `exit-checks` — non-empty list of `{check, result, date}` |
| `waiting-external` requires | `verify-after` — ISO date; the session-start wait check uses this to surface overdue work |
| `artifacts` | Optional list of paths relative to repo root; validator WARNs if they don't exist on disk |

### 3.2 Annotated Example

```yaml
journey:
  offered: 2026-06-12          # date auto-offer was made; prevents re-nagging
  declined: false               # true = never re-offer, even if dimensions drop below 3
  current-phase: 4              # 1-based; informational for the agent, not enforced by validator

phases:
  discover:
    status: complete
    completed: 2026-06-12
    exit-checks:                # required when status is complete
      - check: signal inventory presented to customer
        result: pass
        date: 2026-06-12
      - check: all interpretations confirmed or rejected
        result: pass
        date: 2026-06-12
      - check: decisions written to my-org/context.md
        result: pass
        date: 2026-06-12

  dimensions:
    status: complete
    artifacts:
      - onboarding/templates/collector.py.tmpl  # example of a repo-relative path
    exit-checks:
      - check: validator passes on all starter dimensions
        result: pass
        date: 2026-06-13
      - check: dimensions published and confirmed in CloudZero UI
        result: pass
        date: 2026-06-13

  shared-spend:
    status: complete
    matrix-updated: 2026-06-13
    exit-checks:
      - check: shared-spend matrix presented and confirmed
        result: pass
        date: 2026-06-13
      - check: per-bucket classification confirmed (splittable vs needs telemetry)
        result: pass
        date: 2026-06-13
      - check: allocation loop order chosen
        result: pass
        date: 2026-06-13

  allocation:
    status: in_progress         # the phase itself is in_progress while the loop runs
    per-dimension:
      Team:
        status: skipped
        reason: fully covered by tags — no unallocated spend under this lens
      Product:
        status: complete
        method: proportional-to-direct-spend
        exit-checks:
          - check: AllocateByRules dimension validates without ERROR
            result: pass
            date: 2026-06-14
          - check: allocated view confirmed in CloudZero UI
            result: pass
            date: 2026-06-14
      Customer:
        status: waiting-external          # requires verify-after
        stream: tenant-usage
        collector-deployed: 2026-06-14
        verify-after: 2026-06-16          # session-start wait check uses this date

  unit-cost:
    status: not_started

decisions:
  - "Account-name tokens prod/dev/stg confirmed to mean environment (2026-06-12)"
  - "tenant → product mapping provided, persisted to my-org/context.md (2026-06-13)"
```

**Informational fields.** Fields beyond those in the table above (`decisions`, `completed`, `matrix-updated`, `stream`, `reason`) are informational — write them freely for context; the validator does not check them. Only the table's structural rules are enforced.

**Never invent statuses.** The validator rejects anything not in the valid-values table above. `pending`, `done`, `blocked` are not valid.

---

## 4. The Five-Part Phase Contract

Every phase doc follows this contract. The agent follows it for every phase, without skipping parts.

### 4.1 Entry Criteria

What must exist before starting this phase. Check before proceeding; block and explain if unmet.

### 4.2 Agent-Gathered Inputs

Everything the data can answer, the agent answers itself — via MCP queries, file parsing, and the existing auto-populate machinery. **Never ask the customer for account IDs, tag keys, resource patterns, or anything queryable from the data.** Query first; ask only what the data cannot tell you.

### 4.3 Human Questions

The short list of things only the customer can answer: team ownership, business goals, how shared costs should be split, whether an interpretation is correct. Ask one at a time. Offer concrete candidates drawn from the data rather than open-ended prompts.

### 4.4 Deliverables

Named artifacts: signal inventory, dimension working files, stream spec, collector script. Record artifact paths in the state file under `artifacts`.

### 4.5 Exit Criteria and Recording Rule

**Every exit-criteria check and its result is written to the state file at the transition. Only then flip status to `complete` or `skipped`.**

The validator enforces that `exit-checks` is a non-empty list of `{check, result, date}` entries when status is `complete`. A loosely-following agent that flips to `complete` without recording exit-checks leaves a state file that fails `--check-integrity`. That failure is the deterministic backstop.

For `skipped` phases or `per-dimension` entries: the validator does not require exit-checks. Record a `reason` field so the journey can offer to revisit the skipped item on resume: "We skipped shared spend under Customer — want to come back to it?"

For `waiting-external` phases: record `verify-after` (a date the customer and agent agree on, usually 2–7 days for telemetry to accumulate). The session-start wait check uses this date. Do not flip status to `complete` until the wait check passes.

After every state-file write: run `python3 costformation-brain/validator/lint.py --check-integrity` and fix ERRORs.

---

## 5. Narration Rule

At the start of every phase (initial entry and any resume), announce:

1. Phase N of 5 and its name.
2. What will be produced (the phase's deliverables).
3. What done looks like (the phase's exit criteria in one sentence).
4. Show the phase doc's worked example so the customer sees the destination before the work begins.

Example:

```
Phase 3 of 5: Shared Spend Matrix.

We'll produce a cross-dimension matrix showing every shared-cost bucket,
its monthly spend, and which of your dimensions has it allocated vs
unallocated. Done means: every bucket classified, loop order chosen,
and the matrix recorded in the state file.

Here's what a finished matrix looks like for a typical customer:
[worked example from phase-3-shared-spend.md]
```

Do not skip the worked example. Customers need to see the destination to give useful confirmation.

---

## 6. Durable Knowledge Split

| What | Where it lives | Rule |
|---|---|---|
| Journey position, phase statuses, exit-check results, wait-check dates, artifact paths | `my-org/onboarding-state.yaml` | Agent writes; validator checks |
| Business facts: team-to-account mappings, confirmed interpretations, customer decisions, org goals, CSVs, org charts | `my-org/context.md` | Append-only — never overwrite existing content; only add under relevant section headings |

**When the customer provides a business fact during any phase, append it to `my-org/context.md` immediately.** Do not rely on conversation context to carry it forward. The next session will not remember it otherwise.

The state file holds mechanics. `context.md` holds knowledge. Never conflate them.

---

## 7. Phase Routing Table

| Phase | Phase doc | Required corpus files |
|---|---|---|
| `discover` | `onboarding/phase-1-discover.md` | `sources.md`, `my-org/index.yaml`, `my-org/context.md`, `my-org/` detail files |
| `dimensions` | `onboarding/phase-2-dimensions.md` | `performance-rules.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md`, `examples/index.yaml`, `examples.md`, `my-org/index.yaml`, `my-org/context.md` |
| `shared-spend` | `onboarding/phase-3-shared-spend.md` | `allocation-design.md`, `my-org/index.yaml`, `my-org/context.md` |
| `allocation` | `onboarding/phase-4-allocation.md` | `performance-rules.md`, `allocation-design.md`, `telemetry.md`, `sources.md`, `conditions-and-transforms.md`, `dimension-types.md`, `examples.md`, `my-org/context.md` |
| `unit-cost` | `onboarding/phase-5-unit-cost.md` | `telemetry.md`, `sources.md`, `allocation-design.md`, `my-org/context.md` |

**Before any phase, also read the phase doc itself in full.** The routing table lists corpus prerequisites; the phase doc contains the behavioral contract for that phase.

For phases that generate CostFormation YAML (2, 4, 5): follow the full pre-generation checklist from SKILL.md — including MCP query, my-org/ freshness check, performance-rules.md, allocation-design.md (for allocation phases), examples/index.yaml pattern check, and the working-file workflow (timestamped backup + change sub-folder). Validate with `lint.py` before presenting YAML; fix all ERRORs.

---

## Integration Points

- **SKILL.md** — contains a routing-table row pointing here for onboarding entry phrases and a trigger rule.
- **Agent instruction files** (CLAUDE.md, AGENTS.md, .cursorrules, copilot-instructions.md) — contain the auto-offer rule in startup checks and the explicit-entry phrase list.
- **`validator/rules/onboarding_state.py`** — enforces schema: valid phase names, valid statuses, exit-checks required on `complete`, verify-after required on `waiting-external`, artifact paths validated.
- **`validator/telemetry_check.py`** — validates telemetry payloads in phase 4 before the customer deploys a collector. Run it before recording `waiting-external`.
- **`onboarding/templates/collector.py.tmpl`** — customized per customer in phase 4; the agent fills in CONFIG constants and `collect_usage()`, the customer deploys and runs it.
