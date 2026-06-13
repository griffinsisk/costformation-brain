# Phase 3 — Shared Spend Matrix

**Phase 3 of 5.** Build the cross-dimension shared-spend matrix: for every
detected shared-cost bucket, show its monthly spend and allocation status under
each published dimension. Classify each bucket. Choose the loop order for
phase 4.

Done means: matrix presented and confirmed, per-bucket classification agreed,
loop order chosen, and all three recorded in the state file.

---

## Core Principle

**Sharedness is a property of a resource under a lens, not of the resource
itself.**

A shared RDS cluster can be fully attributable under the Team dimension (every
team tagged their connections) while being the largest unallocated bucket under
the Product dimension (no product tags on the same resources). A Bedrock API
endpoint may be unallocated under all three dimensions simultaneously. The
matrix makes these per-lens facts visible before any allocation work begins.

Do not assume a resource is shared everywhere just because it is shared
somewhere.

---

## 4.1 Entry Criteria

1. **At least one dimension published** — `my-org/onboarding-state.yaml` shows
   `phases.dimensions.status: complete` with at least one dimension confirmed
   visible in CloudZero.
2. **MCP connected** — the matrix is computed from live data. Detection queries
   require the CloudZero MCP; without it the matrix cannot be built.

Block and explain if either condition is unmet.

---

## 4.2 Agent-Gathered Inputs — Detection Catalog

Run all seven detection queries via MCP. Do not ask the customer to identify
shared spend. The data answers this; the customer confirms classifications.

Recompute the full catalog at each loop iteration (phase 4 adds dimensions;
they slot into the matrix automatically).

### 1. "Not in Dimension" spend per published dimension

Query each published custom dimension for spend that falls into the implicit
"Not in Dimension" bucket (no rule matched). This is the primary signal for
unallocated spend under a given lens.

- For each dimension: query `CZ:Defined:<DimensionId>` grouped by value;
  charges with no value (or value = "Not in Dimension") are the unallocated
  pool under that lens.
- Report dollar amount and dominant services in the unallocated pool.

### 2. Single-account services consumed by many teams

Query services where spend originates from one or a small number of accounts
but those accounts serve multiple teams (cross-referencing the Team dimension
if it exists, or account ownership from my-org/).

Typical examples: a shared data-platform account running RDS, Redshift, or
S3 used by all engineering teams; a shared networking account running NAT and
Transit Gateway.

### 3. Shared Kubernetes clusters

Query K8s cost data via MCP. **Check whether the CloudZero K8s agent is
already splitting cluster costs before proposing telemetry.** If the K8s
agent is active, cluster costs may already be attributed to namespaces or
workloads, making them "covered" under a Team or Product lens. Only flag
as unallocated if the agent's attribution does not satisfy the lens.

Report: cluster name, total $/mo, agent-attributed fraction vs unattributed
fraction, and which dimensions the attributed fraction covers.

### 4. NAT gateways and inter-AZ data transfer

Query `Service: AmazonVPC` and related data transfer line items. These are
frequently shared-infrastructure costs with no tagging at the source.

Note: NAT and data transfer are often low-value per consumer but high-volume
in row count. Flag for the expansion-factor advisory (see §4.4.3) before
recommending allocation.

### 5. Support charges and enterprise fees

Query AWS Support, marketplace enterprise fees, and CloudFront Dedicated IPs.
These are almost always organization-level costs with no natural per-team
split signal. Proportional-to-direct-spend is typically the correct allocation
method (phase 4 rung 1 — no telemetry required).

### 6. LLM API spend

Query `Service: AmazonBedrock` and any SaaS connections (OpenAI, Anthropic
via AWS Marketplace, etc.). LLM API charges are frequently significant and
untagged because the calling application, not the API, holds the team and
product context.

Report: total $/mo, model breakdown, and whether any `Tag:team` or
`Tag:product` values are present on the line items.

### 7. Observability platforms

Query any observability SaaS connections (Datadog, New Relic, Splunk, etc.)
configured in the CloudZero org. These are typically flat subscription charges
or usage charges billed at the organization level.

Report: platform name, total $/mo, whether any per-team split signal exists
(e.g., a cost-allocation dimension or tagged usage breakdown from the vendor).

---

## 4.3 The Cross-Dimension Matrix

Build this table from the detection catalog results. Recompute from MCP at
each loop iteration.

**Format:**

| Shared bucket | $/mo | Dim-1 (e.g. Team) | Dim-2 (e.g. Product) | Dim-3 (e.g. Customer) |
|---|---|---|---|---|
| \<bucket name\> | \<amount\> | covered (\<signal\>) / unallocated | ... | ... |

**Cell values:**
- `covered (tag)` — spend is allocated; a tag-based rule is the signal
- `covered (account)` — spend is allocated; account-name matching is the signal
- `covered (K8s agent)` — spend is allocated by the CloudZero K8s agent
- `covered (rule)` — spend is allocated by a CostFormation rule (non-tag)
- `unallocated` — no rule covers this spend under this lens

Cells may combine, e.g. `covered (tag) — 80%, unallocated — 20%` if partial
coverage exists.

**Matrix rules:**
- Add a row for every bucket surfaced by the detection catalog with $/mo > 0.
- Add a column for every published dimension, including any added after the
  matrix was first built.
- Leave the matrix blank for dimensions that don't apply to a bucket (rare;
  explain when it occurs).

---

## 4.4 Classification

After building the matrix, classify each bucket:

| Classification | Meaning |
|---|---|
| **Splittable with existing signals** | At least one dimension already has a signal (tag, account, K8s) that could allocate this bucket — the phase 4 work is writing the CostFormation rule |
| **Needs a usage signal** | No existing billing signal allocates this bucket for the target lens — phase 4 will require telemetry co-design |

Record classification alongside the matrix. The customer confirms or
corrects each one.

---

## 4.5 Three Matrix-Driven Behaviors

### Behavior 1: Informed Prioritization

Present unallocated dollars per lens. The customer picks which dimension's
loop (phase 4) to run first, guided by where the largest unallocated spend
sits.

**"Nothing shared under this lens" is a legitimate skip.** If Team already
covers 98% of spend with no shared buckets, record
`phases.allocation.per-dimension.Team.status: skipped` with reason
`fully covered by tags — no unallocated spend under this lens`. Do not
force work that the data says is not needed.

### Behavior 2: Correlation Surfacing

When a bucket is unallocated under **multiple** dimensions simultaneously,
apply the **collect-at-the-finest-grain rule**:

> Capture usage at the finest grain available (e.g., per-tenant). Coarser
> splits — per-product, per-team — are **derived** from the finest grain via
> customer-confirmed mappings (tenant → product, tenant → team). One
> collector sends multiple streams; each stream feeds one allocation
> dimension.

The matrix reveals this opportunity before any collector is built. Example:
Bedrock spend unallocated under Team, Product, and Customer simultaneously.
The finest grain is per-tenant (the application calling Bedrock knows which
tenant made the request). Collect per-tenant; derive per-team and per-product
via mappings the customer confirms. One collector, three streams.

**When this applies:** record the derivation mappings in
`my-org/context.md` immediately. Append under a heading such as
`## Derivation Mappings` — tenant-to-product and tenant-to-team mappings
must survive session boundaries because they are needed when writing the
collector and the stream specs in phase 4.

### Behavior 3: Expansion-Factor Advisory

Each allocation dimension multiplies Snowflake rows independently.
From `allocation-design.md`:

> **Formula:** `targeted line items × allocation elements = total rows`

Flag buckets where allocation costs more in processing than it returns in
analytical value. Concrete example: allocating NAT gateway charges
(`AmazonVPC` data transfer) across 200 customers produces
`N line items × 200 = 200N rows` in Snowflake for a cost that may be
$200/mo total ($1/customer/month). Recommendation: leave this bucket
unallocated under the Customer lens; record the advisory in the state file so
the customer can revisit it.

Present the advisory as part of classification, not as a block — the customer
picks. Flag it; don't mandate it.

---

## 4.6 Human Questions

Ask one at a time. Offer concrete candidates from the data.

1. **Confirm bucket classifications.** For each bucket, present the
   classification (`splittable` or `needs usage signal`) with the evidence.
   "Shared RDS is unallocated under Product — no product tag exists on those
   instances. I've classified it as 'needs a usage signal' for the Product
   lens. Does that match your expectation?"

2. **Confirm or correct derivation mappings.** When the finest-grain rule
   applies, present the proposed mapping and ask the customer to confirm or
   supply it. "Per-tenant Bedrock usage would derive Team via a tenant→team
   mapping. Do you have that mapping? I can accept a CSV or a list."

3. **Choose loop order.** Present the unallocated dollars per lens and ask
   which dimension's loop to run first. "Largest unallocated buckets: Product
   ($52k), Customer ($43k), Team ($8k). Which lens do you want to allocate
   first?"

Do not ask the customer for account IDs, service names, tag keys, or anything
the detection catalog already surfaced.

---

## 4.7 Deliverables

1. **The matrix** — bucket × dimension table with $/mo and cell values as
   described in §4.3. Record at `shared-spend matrix` in the state file
   under `matrix-updated: <ISO date>`.
2. **Per-bucket classification** — splittable vs needs usage signal, one row
   per bucket.
3. **Chosen loop order** — ordered list of dimension names for phase 4; skips
   noted with reason.

Record the loop order in the state file as the order of `per-dimension`
entries under `phases.allocation`.

---

## 4.8 Exit Criteria and Recording Rule

Record each check in the state file **before** flipping status to `complete`.

```yaml
shared-spend:
  status: complete
  matrix-updated: <ISO date>
  exit-checks:
    - check: shared-spend matrix presented and confirmed
      result: pass
      date: <ISO date>
    - check: per-bucket classification confirmed (splittable vs needs telemetry)
      result: pass
      date: <ISO date>
    - check: allocation loop order chosen and recorded
      result: pass
      date: <ISO date>
```

After writing the state file, run:

```bash
python3 costformation-brain/validator/lint.py --check-integrity
```

Fix all ERRORs before proceeding to phase 4.

---

## Worked Example

A customer has three published dimensions: Team, Product, Customer. Detection
catalog surfaces three shared-spend buckets.

**Matrix:**

| Shared bucket | $/mo | Team | Product | Customer |
|---|---|---|---|---|
| Shared RDS cluster | $48,000 | covered (tag) | unallocated | unallocated |
| Bedrock API spend | $31,000 | unallocated | unallocated | unallocated |
| NAT gateway / data transfer | $12,000 | unallocated | unallocated | unallocated |

**Classification:**

| Shared bucket | Classification | Notes |
|---|---|---|
| Shared RDS cluster | Team: splittable (tag `db-team` present); Product: needs usage signal; Customer: needs usage signal | Tag covers Team; no product or tenant signal on RDS instances |
| Bedrock API spend | All lenses: needs usage signal | No tag on Bedrock line items; caller context is in application logs |
| NAT / data transfer | All lenses: needs usage signal | No tagging possible on NAT line items |

**Expansion-factor advisory:**

NAT/$12k across 200 customers: `~500 VPC line items × 200 = 100,000 rows` for
$12k total ($60/customer/month). Recommendation: leave unallocated under
Customer. Team and Product may be worth allocating if NAT correlates with
high-traffic services (check with customer).

**Finest-grain opportunity:**

Bedrock is unallocated under all three lenses. If the application calling
Bedrock knows the tenant, collect at per-tenant granularity. Derive Team
and Product from a tenant→team and tenant→product mapping the customer
provides. One Bedrock collector, three streams. Record mappings in
`my-org/context.md`.

**Chosen loop order** (customer decision, guided by unallocated dollars):

1. Product — $79k unallocated (Shared RDS + Bedrock)
2. Customer — $79k unallocated, but NAT advisory recommends deferring NAT
3. Team — $43k unallocated (Bedrock + NAT); Shared RDS already covered

---

## Go Deeper

- `allocation-design.md` — expansion-factor formula, `ForEachElementOf` for
  reducing row multiplication, overlap investigation
- https://docs.cloudzero.com/docs/splitting-shared-costs
