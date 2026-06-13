# Phase 2 — Suggest Dimensions

**Phase 2 of 5.** Cross-reference the confirmed signal inventory from phase 1
against the candidate dimension catalog. Produce a ranked starter-set proposal.
Build selected dimensions through the existing write flow.

Done means: starter dimensions validated (lint passes), published to CloudZero,
confirmed visible by the customer in the UI, and recorded in the state file.

---

## Entry Criteria

1. **Phase 1 complete** — `my-org/onboarding-state.yaml` shows
   `phases.discover.status: complete` with recorded exit-checks.
2. **Signal inventory exists** — the confirmed inventory table (with coverage
   percentages and confirmed interpretations) was produced in phase 1. The agent
   carries it forward; do not re-query what phase 1 already confirmed.

Block and explain if either condition is unmet.

---

## Candidate Dimension Catalog

Every new CloudZero org should consider these seven concepts. Cross-reference
the signal inventory against this table in both directions:

- **Signals match a concept → candidate for the ranked proposal.**
- **Concept has no signal → gap finding; route to phase 4 for telemetry co-design.**

Gaps are first-class findings, not failures.

| Concept | Why it matters | Typical signals | Starting pattern |
|---|---|---|---|
| Environment | Separates prod spend from non-prod waste; answers "how much are we spending on dev/staging?" | `Tag:environment`, `Tag:env`, account name tokens (`prod`, `dev`, `stg`, `staging`, `sandbox`), resource name suffixes | `tag-based-environment.yaml` |
| Team / Owner | Drives accountability and showback; answers "which team owns this spend?" | `Tag:team`, `Tag:owner`, K8s namespace prefix, K8s label `team`, dedicated account per team | `k8s-namespace-to-team.yaml`, `tag-based-multi-source.yaml`, `account-mapping-basic.yaml` |
| Product | Enables product P&L and roadmap cost tradeoffs; answers "what does it cost to run product X?" | `Tag:product`, K8s namespace or label `app.kubernetes.io/part-of`, account name tokens that match product names | `k8s-label-to-product.yaml` |
| Application / Service | Service-level cost visibility for rightsizing and build-vs-buy decisions | Resource names, K8s workload names, `Tag:app`, `Tag:service`, `Tag:component` | `tag-based-multi-source.yaml` |
| Customer / Tenant | COGS per customer, unit cost, and pricing model validation; answers "what does it cost to serve customer X?" | Usually **no billing signal** — tenant identity lives in app-layer telemetry, not in billing data | `allocation-telemetry-basic.yaml` |
| Business Unit | Executive cost rollups and portfolio-level P&L; answers "how much does each business unit spend?" | Account hierarchy, `Tag:business-unit`, `Tag:bu`, account name tokens for org divisions | `hierarchy-parent-child.yaml` |
| Cost Center | Finance chargeback and budget mapping; answers "which cost center owns this charge?" | Account-to-cost-center mapping (human-provided CSV), `Tag:cost-center`, `Tag:cc`; rarely self-service from billing data alone | `account-mapping-large-scale.yaml`, `tag-groupby-with-fallback.yaml` |

---

## Two-Directional Matching Rule

**Signals → catalog:** for each signal in the confirmed inventory, find the
catalog concept it most closely maps to. That concept becomes a candidate.

**Catalog → signals:** for each catalog concept, check whether a matching
signal exists. If not, record it as a gap:

```
Gap: Customer/Tenant — no signal exists in tags, accounts, resources, or K8s.
Allocating by customer requires app-layer telemetry. Flagged for phase 4.
```

Report all gaps to the customer before building anything. Gaps narrow scope;
they are not a sign that something went wrong.

---

## Ranked Starter-Set Proposal Format

Present candidates ranked by estimated coverage × business value before writing
any YAML. Each candidate entry:

| Field | Content |
|---|---|
| **Concept** | Catalog name |
| **Evidence** | What signal(s) were found and in which source (tag key + coverage %, account name pattern + count, K8s namespace values, etc.) |
| **Estimated coverage** | % of total monthly spend the dimension will classify, based on signal coverage |
| **Starting pattern** | Which `examples/patterns/` file to start from |
| **Cannot infer** | What the agent cannot determine from data alone (element naming preferences, whether two concepts should be merged into one dimension, etc.) |

**No YAML until the customer picks candidates from the proposal.**

---

## Human Questions

Ask only what the data cannot answer. Examples (adapt to what you found):

> "I found signals for Environment, Team, and Product. Which would you like to
> build first — or should I build all three as a starter set?"

> "For the Team dimension, the tag values are `payments`, `platform`, `data`,
> `infra`. Should I use those exact strings as element names, or would you prefer
> different display names?"

> "The account-name tokens for Business Unit are `corp` and `ent`. Do those map
> to named business units — or are they something else?"

> "Customer/Tenant has no signal in billing data. This dimension needs telemetry.
> Want to set it up now (phase 4) or skip it for now?"

Ask one question at a time. Offer concrete candidates; never ask open-ended
"what dimensions do you want?" prompts.

---

## Build Step

Selected dimensions go through the existing SKILL.md write flow unchanged — pre-generation checklist, timestamped backup + change sub-folder, validator, present. Record the working-folder paths under `artifacts` in the state file.

---

## Deliverables

- **Ranked starter-set proposal** (in conversation) — all candidates with
  evidence, coverage, pattern, and what cannot be inferred.
- **Gap list** (in conversation) — catalog concepts with no signal, each with a
  one-line route (phase 4 telemetry, or skip).
- **Working files** for each selected dimension — clean YAML + comments file in
  a timestamped sub-folder. Paths recorded in the state file.
- **Updated `my-org/context.md`** — append naming decisions, element mappings,
  and any business-rule clarifications the customer provided.

---

## Exit Criteria and Recording Rule

Run all checks before flipping status to `complete`. Write each result first.

```yaml
phases:
  dimensions:
    status: complete
    artifacts:
      - environment-dimension_2026-06-13/
      - team-dimension_2026-06-13/
    exit-checks:
      - check: ranked proposal presented and candidates selected
        result: pass
        date: <ISO date>
      - check: validator passes (no ERRORs) on all starter dimensions
        result: pass
        date: <ISO date>
      - check: dimensions published and confirmed visible in CloudZero UI
        result: pass
        date: <ISO date>
      - check: decisions and naming choices written to my-org/context.md
        result: pass
        date: <ISO date>
```

After writing, run:

```bash
python3 costformation-brain/validator/lint.py --check-integrity
```

Fix all ERRORs before proceeding to phase 3.

---

## Worked Example — 3-Candidate Ranked Proposal

A generic multi-account AWS org with K8s. Signal inventory carried in from
phase 1 (anonymized — no real customer names):

**Phase 1 inventory (abbreviated):**
- `Tag:environment` — values `prod`, `staging`, `dev` — 74% coverage
- Account name tokens `prod`/`dev`/`stg` — 18 of 22 accounts — ~82% of accounts
- `Tag:team` — 6 values (`payments`, `platform`, `data`, `infra`, `ml`, `shared`) — 71% coverage
- K8s namespaces — `production`, `staging`, `dev`, `data-platform` — 22% of spend
- Gap: Customer — no signal in tags, accounts, resources, or K8s

---

**Proposal presented to customer:**

---

### Candidate 1 — Environment (recommended first)

| | |
|---|---|
| **Evidence** | `Tag:environment` (74% coverage) + account-name tokens `prod`/`dev`/`stg` on 18/22 accounts. Combined estimated coverage: ~88% of spend. |
| **Estimated coverage** | ~88% |
| **Starting pattern** | `tag-based-environment.yaml` |
| **Cannot infer** | Whether K8s namespaces (`production`, `staging`) represent the same environment concept as the tag — need confirmation. Whether the remaining 12% is untagged or intentionally excluded. |

---

### Candidate 2 — Team / Owner

| | |
|---|---|
| **Evidence** | `Tag:team` with 6 values (`payments`, `platform`, `data`, `infra`, `ml`, `shared`) at 71% coverage. K8s namespace prefixes match 4 of the 6 team names — adds ~8% more. Combined: ~64% direct, ~79% with K8s. |
| **Estimated coverage** | ~64–79% |
| **Starting pattern** | `k8s-namespace-to-team.yaml` (K8s path), `tag-based-multi-source.yaml` (combined tag + K8s + account) |
| **Cannot infer** | Whether `shared` is a real team or a catch-all; whether accounts not covered by the tag belong to one of the 6 teams or a new one. |

---

### Gap — Customer / Tenant

| | |
|---|---|
| **Signal** | None — no tenant ID in tags, account names, resource names, or K8s labels. |
| **Route** | Allocating by customer requires sending app-layer telemetry (API call counts, query counts, or similar) to CloudZero. This is phase 4 work. Flag for later. |

---

**Agent narration:**

```
Phase 2 of 5: Dimension Suggestions.

I found strong signals for 2 dimensions and 1 gap:

1. Environment (~88% coverage) — tag + account name tokens
2. Team (~64–79%) — tag + K8s namespaces

Gap: Customer/Tenant — no billing signal; needs telemetry (phase 4).

Which candidates would you like to build? I can start with Environment,
build all three at once, or skip one. No YAML until you pick.
```

---

## Go Deeper

- `dimension-types.md` — choosing between Group, GroupBy, Allocation, and Metadata types
- `examples/index.yaml` — full pattern library with use_when metadata
- `performance-rules.md` — DefaultValue expansion factor, rule ordering, Snowflake cost impact
- https://docs.cloudzero.com/docs/dimensions — CloudZero dimension concepts and UI walkthrough
- https://docs.cloudzero.com/docs/dimension-patterns — catalog of common dimension patterns
