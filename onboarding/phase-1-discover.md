# Phase 1 — Discover

All `my-org/` paths in this document are relative to the customer workspace
root, not the `costformation-brain` repository.

**Phase 1 of 5.** Inventory every billing signal across all six sources. Confirm
interpretations. Produce a signal inventory table the agent carries into phase 2.

Done means: inventory presented, every interpretation confirmed or rejected,
decisions recorded in `my-org/onboarding-state.yaml` and `my-org/context.md`,
and `my-org/` detail files written via the auto-populate machinery.

---

## Entry Criteria

Check both before starting. Block and explain if either is unmet.

1. **MCP connected** OR a costformation file (`.cz.yaml` / `.yaml`) is present in
   the workspace. At least one source of billing signal must exist.
2. **`my-org/` is populated or populatable.** If `accounts.yaml`, `tags.yaml`, or
   `dimensions.yaml` are empty (`last-synced: never`), run the auto-populate
   machinery from CLAUDE.md before proceeding. Do not proceed with empty detail
   files — the inventory will be incomplete.

If MCP is not connected, skip signal sources that require live queries (tags,
K8s, service spend). Note the gap in the inventory and proceed with what the
costformation file provides.

---

## Agent-Gathered Inputs

Query all six sources before presenting anything. Do not ask the customer for
account IDs, tag keys, resource patterns, or anything derivable from the data.

### Signal 1 — Tags

Query via MCP: tag keys present in the org, their value sets, and coverage
percentage per key (what fraction of spend has this tag on the resource).

Derive from output:
- Which keys have coverage > 50% (meaningful signal)
- Which keys have value patterns that suggest concept (e.g. `environment` →
  `prod/staging/dev`; `team` → `payments/platform/data`)
- Which keys have low coverage but high-value spans (useful partial signal)

Record each tag key as a candidate row in the inventory with its coverage %.

### Signal 2 — Account Names

Pull account list from MCP or `my-org/accounts.yaml`. Tokenize each name on
delimiters `[-_ /]` and case boundaries. Look for:

- **Environment tokens:** `prod`, `production`, `dev`, `development`, `staging`,
  `stg`, `qa`, `test`, `sandbox`, `sbx`, `nonprod`
- **Team/product tokens:** any recurring token across ≥ 3 account names that
  is not an environment token (e.g. `payments`, `data`, `platform`, `infra`)
- **Org-level patterns:** numeric suffixes (`-001`, `-002`) that indicate
  account-per-tenant or account-per-environment patterns

Report: "X of Y account names contain [token set] — candidate for [concept]."
Record total account count and which accounts do NOT match any pattern (ungrouped).

### Signal 3 — Resource Names

Query `CZ:Defined:ResourceSummaryDisplay` via MCP. This dimension groups related
resources at low cardinality and is preferred for resource-name pattern matching.

Scan returned values for:
- Environment tokens (same list as Signal 2)
- Team or product tokens embedded in resource names (e.g. `payments-rds`,
  `data-eks-cluster`, `platform-cache`)
- Tenant or customer identifiers (e.g. `tenant-abc`, `customer-xyz`, `acme-`)

Only add resource-name patterns to the inventory when they cover spend that tags
and accounts do NOT already classify. Do not add redundant conditions — if tags
already catch 100% of a concept's spend, resource names are not worth adding.

Report count of distinct patterns found and estimated % of spend they touch.

### Signal 4 — K8s Labels and Namespaces

If K8s cost is present (check `my-org/index.yaml` for `has_k8s: true` or query
MCP for K8s spend > $0):

- Query `K8s:Namespace` values — namespace names frequently encode environment
  (`production`, `staging`, `dev`) or team (`payments`, `platform`)
- Query `K8s:Label:<LabelName>` for common labels: `app`, `team`, `env`,
  `environment`, `component`, `tier`, `service`
- Query `K8s:Workload` for workload-name patterns

If no K8s spend detected, record "K8s — not present" in the inventory and skip.

### Signal 5 — Existing Dimensions

Parse the costformation file and query MCP for dimensions already published.
For each existing dimension:

- What concept does it classify (name is often sufficient — `Environment`,
  `Team`, `CostCenter`)
- What source does it use (`Tag:`, `Account`, `K8s:Namespace`, etc.)
- Estimated coverage (from MCP if connected, otherwise note as unknown)

Existing dimensions are signal: they tell you what concepts the customer already
tracks and what gaps remain. A dimension covering only 60% of spend is a partial
signal, not a solved problem.

### Signal 6 — Service Spend Distribution

Query MCP for spend by cloud service (top 10–15 by monthly cost). This weights
the ranking in phase 2 — a dimension concept that only applies to 2% of spend is
lower priority than one that touches 60%.

Derive:
- Total monthly spend (approximate)
- Top services and their % of total
- Which services are likely shared (RDS, ElastiCache, S3, EKS control plane,
  NAT Gateway, Support, Bedrock) vs directly attributable

Record as a summary row in the inventory: "Top service: EC2 (42%), RDS (18%),
S3 (11%) — RDS and NAT are shared-spend candidates for phase 3."

---

## Human Questions

**Every observation cites the signal that produced it and ends in a confirmation
question, never an assertion.**

Do not tell the customer what a signal means. Ask whether your interpretation is
correct. Ask one question at a time. Offer the concrete interpretation drawn from
the data, not an open prompt.

Example confirmations (adapt to what you actually found):

> "18 of 22 account names contain prod/dev/stg tokens — does that encode
> environment?"

> "The tag key `team` has 73% coverage and values matching 6 distinct team names
> — does this tag reliably identify team ownership?"

> "K8s namespaces include `production`, `staging`, `dev` — same as the account
> tokens. Do they represent the same environment concept, or are they separate?"

> "Resource names under `CZ:Defined:ResourceSummaryDisplay` show a `-prod` /
> `-dev` suffix pattern on 34% of spend not covered by tags or accounts — should
> that be included in the environment signal?"

Record each confirmed interpretation as a decision entry:

```yaml
decisions:
  - "Account-name tokens prod/dev/stg confirmed to mean environment (YYYY-MM-DD)"
  - "Tag 'team' confirmed as team ownership signal; 6 values mapped (YYYY-MM-DD)"
```

Append confirmed facts to `my-org/context.md` under the relevant section heading
immediately — do not rely on conversation context to carry them forward.

---

## Deliverables

**Signal inventory table** — one row per signal found, plus gap rows for catalog
concepts with no signal.

| Signal | Source | Evidence | Coverage | Candidate concept |
|---|---|---|---|---|
| (signal name) | (MCP / costformation / account names) | (what you found) | (% or count) | (concept from phase-2 catalog) |

Gap rows use this form:

| Customer | — | No signal in tags, accounts, resources, or K8s | 0% | Customer/Tenant — telemetry candidate, flag for phase 4 |

Write the table to the conversation. The agent carries it into phase 2
(`phase-2-dimensions.md`) for cross-reference against the candidate catalog.

Record artifact path in the state file under `artifacts` if you write the
inventory to a file. Writing it to conversation only is acceptable for phase 1.

---

## Exit Criteria and Recording Rule

Run all checks before flipping status to `complete`. Write the result of each
check to the state file first — only then flip.

```yaml
phases:
  discover:
    status: complete
    completed: <ISO date>
    exit-checks:
      - check: signal inventory presented to customer
        result: pass
        date: <ISO date>
      - check: all interpretations confirmed or rejected
        result: pass
        date: <ISO date>
      - check: decisions written to my-org/context.md
        result: pass
        date: <ISO date>
      - check: my-org/ detail files written and source-hash current
        result: pass
        date: <ISO date>
```

After writing, run:

```bash
python3 costformation-brain/validator/lint.py --check-integrity
```

Fix all ERRORs before proceeding to phase 2. WARNINGs on missing artifacts are
acceptable if the artifact has not been created yet in this session.

**my-org/ files:** use the existing auto-populate machinery (CLAUDE.md §
"Auto-Populate Org Context"). Do not duplicate the logic here — call it.

---

## Worked Example

A realistic six-signal inventory for a generic multi-account AWS org with K8s.

| Signal | Source | Evidence | Coverage | Candidate concept |
|---|---|---|---|---|
| Account name tokens | Account names | 18 of 22 accounts contain `prod`, `dev`, or `stg` | ~82% of accounts | Environment |
| Tag: `team` | MCP tag query | 6 distinct values (`payments`, `platform`, `data`, `infra`, `ml`, `shared`) — 71% coverage | 71% of spend | Team/Owner |
| Tag: `service` | MCP tag query | 14 distinct values, sparse — 38% coverage | 38% of spend | Application/Service (partial) |
| K8s namespaces | K8s:Namespace | `production`, `staging`, `development`, `data-platform` — present on 22% of spend | 22% of spend | Environment (K8s path) |
| Existing dimension: CostCenter | costformation file | Covers 4 cost centers, ~60% of spend via Account conditions | 60% of spend | Cost Center (already built, partial) |
| Service spend | MCP spend query | EC2 44%, RDS 19%, EKS 12%, S3 9%, NAT 4%, Support 3% — RDS and NAT are shared | 100% (distribution) | Weights ranking; RDS/NAT flag for phase 3 |
| Customer | — | No signal in tags, accounts, resources, or K8s | 0% | Customer/Tenant — telemetry candidate, flag for phase 4 |

The Customer gap row routes to phase 4's telemetry co-design. The agent carries
this table into `phase-2-dimensions.md` for cross-reference against the candidate
catalog and ranked starter set.

---

## Go Deeper

- `sources.md` — all CostFormation source syntax including `CZ:Defined:ResourceSummaryDisplay`
- `my-org/index.yaml` — compact org summary; check `has_k8s`, account count, top signals
- https://docs.cloudzero.com/docs/dimensions — CloudZero dimension concepts and UI
