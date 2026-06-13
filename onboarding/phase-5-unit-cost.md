# Phase 5 — Unit Cost (Optional)

**This phase is optional.** Skipping it is a first-class exit — the journey is complete
without it. If the customer wants to skip, set `unit-cost.status: skipped` with a reason
in the state file and close the journey. Do not push for this phase.

---

## Entry Criteria

- At least one allocation loop from phase 4 is `complete` (or all shared-spend buckets
  under the chosen lens are rule-based with no telemetry pending). In other words: there
  are allocated dimensions to build a unit cost view on top of.
- The customer has indicated they want to proceed.

If neither condition holds, offer to pause here and return when allocation is further along.

---

## Pick a Unit (Human Question)

The data cannot answer this. Ask:

> "What does your business sell — what's one unit of output or consumption? (e.g., a
> customer, a request, a transaction, a workload run, a seat)"

Offer concrete candidates drawn from what you know about the org:
- If phase 4 built a Customer/Tenant dimension → **cost per customer** is the obvious
  first unit.
- If phase 4 built an Application or Product dimension → **cost per request** or
  **cost per workload run** may fit.
- If the customer sells seats or licenses → **cost per seat**.

The business context (what the sales team sells, what the pricing page shows) determines
the right unit. Record the chosen unit in the state file and in `my-org/context.md`.

---

## Demand-Side Stream

Unit cost = allocated cost ÷ demand metric. The agent's job is to get a demand metric
into CloudZero as a telemetry stream.

**Check the state file first.** If phase 4 collected usage at the finest grain (e.g.,
per-tenant request counts), that stream may already exist and already double as the demand
metric. Query the state file's recorded streams (`allocation.per-dimension.*.stream`)
before designing anything new.

If no suitable stream exists, design one using the same sequence as phase 4:

> Follow `phase-4-allocation.md`'s co-design sequence steps 1–6 with the demand metric
> as the value (e.g., request count, transaction count, active customers per day).

Key differences from an allocation stream:
- The "pool element" concept doesn't apply — the demand stream records total demand
  across the org or per element directly.
- Granularity matches the reporting cadence the customer cares about (`DAILY` for most
  unit cost views; `HOURLY` if the customer tracks intraday cost behavior).
- The stream name should make its purpose obvious: `requests-by-customer-v1`,
  `active-users-daily-v1`.

Record `waiting-external` in the state file (with `verify-after`) if the customer needs
to deploy a new collector. The session-start wait check will surface it on the next
session.

---

## The Unit Cost View

Once the demand stream is landing, the unit cost view is built in the CloudZero UI under
**Unit Economics**. The view divides an allocated cost dimension (from phase 4) by the
demand metric stream.

The agent's deliverable ends here — the telemetry and dimensions feeding the view, not
the UI configuration itself. Point the customer at the UI and the docs below.

---

## Exit Criteria and Recording Rule

Before flipping `unit-cost.status` to `complete`, confirm all of the following and record
them in the state file:

```yaml
unit-cost:
  status: complete
  unit: cost-per-customer
  demand-stream: tenant-usage-daily-v1
  exit-checks:
    - check: demand stream landing with expected element names verified via MCP
      result: pass
      date: <ISO date>
    - check: unit metric visible in CloudZero UI (Unit Economics)
      result: pass
      date: <ISO date>
    - check: chosen unit and business context recorded in my-org/context.md
      result: pass
      date: <ISO date>
```

Run `python3 costformation-brain/validator/lint.py --check-integrity` after writing.

**Journey complete.** Once these exit checks are recorded, narrate what was built across
all phases: the dimensions created, the streams deployed, the shared-cost buckets
allocated, and the unit cost metric now visible. Record a summary in `my-org/context.md`.

---

## Worked Example — Cost per Customer (Reusing the Phase-4 Stream)

**Setup:** Phase 4 built a Customer allocation using the `tenant-usage` stream (per-tenant
request counts, `HOURLY`). The customer wants to see cost per customer per day.

**Reuse check:** `allocation.per-dimension.Customer.stream: tenant-usage` is already in
the state file. That stream emits per-tenant counts — it is the demand metric.

No new collector needed. The customer creates a unit economics view in the CloudZero UI
pointing at:
- Allocated cost dimension: the Customer combined view from phase 4
- Demand metric: `tenant-usage` stream, aggregated daily

Result: cost per customer, updated daily, visible in the CloudZero UI. The journey is
complete.

If the stream were hourly and the customer wants a daily view, CloudZero aggregates
automatically in the unit economics configuration — no re-deployment required.

---

## Go Deeper

- https://docs.cloudzero.com/docs/unit-economics
- https://docs.cloudzero.com/docs/tutorial-calculate-unit-cost-metrics
- https://docs.cloudzero.com/docs/unit-metric-case-studies
