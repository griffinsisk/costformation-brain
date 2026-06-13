# Phase 4 — Allocation Loop (per dimension)

**Phase 4 of 5.** For the chosen lens (dimension), walk each of its unallocated shared-cost
buckets up the split-method ladder and build the allocation dimensions. This phase loops —
run it once per dimension with unallocated spend. Done when every bucket is either allocated
or deliberately skipped, the combined view validates, and costs are visible in CloudZero.

---

## Entry Criteria

- Phase 3 (`shared-spend`) is `complete` and the shared-spend matrix is recorded in the
  state file.
- A lens (dimension) has been chosen for this loop iteration. The customer picks from the
  matrix — prioritize by unallocated dollars, not by complexity.
- `onboarding-state.yaml` shows `allocation.status: in_progress` and the chosen dimension
  is present under `per-dimension` (or is about to be added).

If these conditions are not met, return to phase 3.

---

## The Split-Method Ladder

Order by effort. Recommend a rung based on bucket dollar size and the precision the lens
requires. The customer picks — even split is a legitimate starting point.

| Rung | Method | When to recommend |
|---|---|---|
| 1 | CostFormation-native rules — Even or Proportional | Small bucket, or precision isn't required for this lens |
| 2 | Business-metric telemetry | Headcount, seats, revenue share, MAU; changes rarely; monthly granularity is fine |
| 3 | Service usage telemetry | Large bucket, fidelity matters, usage data is available |

**Rung 1** uses `AllocateByRules` with no telemetry pipeline. See
`examples/patterns/allocation-rules-even-split.yaml` (Even method) and
`examples/patterns/allocation-rules-proportional.yaml` (Proportional method). Even split
is never a failure — record it with an "upgrade later" note in the state file under the
dimension's entry and move on. Proportional-to-direct-spend (AllocateByRules, Proportional
method, AcrossElements by the lens dimension) is a solid default when direct-cost ratios
are a reasonable proxy for shared-cost ratios.

**Rung 2** uses the same telemetry pipeline as rung 3 but with `MONTHLY` granularity and
a trivial source (a CSV export or a spreadsheet of headcount numbers). Design the stream
spec and collector the same way; only the granularity and `collect_usage()` implementation
differ.

**Rung 3** applies when the bucket is large enough (>~$5k/mo is a useful threshold) and
a real usage signal is available. The metric interview guide below tells you what to ask for.

**Expansion-factor advisory:** before recommending rung 3 for a small bucket or a
high-cardinality lens (e.g., 200 customer tenants), flag the expansion cost:
`targeted line items × allocation elements = Snowflake rows`. See `allocation-design.md`.
When the processing cost exceeds the allocation value, recommend even split with an
upgrade note instead.

---

## Metric Interview Guide (Rungs 2 and 3)

Ask "do you have X?" DOWN this list for the relevant shared-cost type — never ask
"what metrics do you have?" (open-ended prompts produce vague answers).

| Shared-cost type | Ask for first (ideal signal) | Then ask for (acceptable proxy) | Where it typically lives |
|---|---|---|---|
| Shared RDS / database | Queries or rows processed per tenant per hour | Connections per service per hour | App logs, DB proxy (RDS Proxy, PgBouncer), `pg_stat_statements` |
| LLM APIs (Bedrock, OpenAI) | Tokens per team or per feature (input + output) | Requests per team | API gateway logs, K8s labels on caller workloads, `CZ:Defined:GenAI_TokenType` |
| Observability (Datadog, Grafana) | Ingested GB per service | Host count per team | Vendor usage API (`/v1/usage/logs-by-retention` etc.) |
| Shared K8s cluster | Verify CloudZero K8s agent is deployed — it usually covers this | Namespace cost share | CloudZero K8s agent (check before building telemetry) |
| NAT / data transfer | Bytes per source service from VPC flow logs | Even split (often not worth more) | VPC flow logs, CloudWatch bytes metrics |
| Support / enterprise fees | Proportional-to-direct-spend (rung 1, AllocateByRules Proportional) | Even split (rung 1) | n/a — use `AllocateByRules`, no telemetry needed |

**Reuse rule:** before designing a new stream, check the state file for streams already
flowing under other dimensions. The finest-grain rule from phase 3 means one collector may
already emit per-tenant data — a derivation mapping (tenant → team, tenant → product)
can produce a second stream from the same source without a second collector. Ask the
customer to confirm the mapping; append it to `my-org/context.md`.

---

## Telemetry Co-Design Sequence (Rungs 2 and 3)

Run these steps in order. Do not flip `waiting-external` until step 5.

### Step 1 — Hidden target dimension

Create a hidden target dimension that defines the cost pool and the allocation targets.
The "pool" element becomes the filter anchor for telemetry records; the target elements
become the `element_name` values. See STEP 1 in
`examples/patterns/allocation-telemetry-basic.yaml`.

Rules for this dimension:
- `Hide: true` — never shown in the UI as a standalone view
- No `DefaultValue` — unmatched charges stay "Not in Dimension" and are never allocated
  (see `allocation-design.md` Rule 6)
- Elements include: one element per allocation target **plus** one pool element (e.g.,
  `Bedrock`) that the telemetry filter will reference

Validate before proceeding: `python3 costformation-brain/validator/lint.py <costformation-file>`

### Step 2 — Stream spec

Write down before touching any YAML:

| Field | Value |
|---|---|
| Stream name | Descriptive, version-suffixed (e.g., `bedrock-tokens-by-env-v1`) |
| Target dimension ID | The hidden dim from step 1 |
| Pool element | The element name telemetry records will filter to (e.g., `Bedrock`) |
| Allocation targets | Element names telemetry records will use as `element_name` |
| Filter key | `custom:<Dimension UI Name>` — the `Name:` field of the hidden dim, NOT the YAML ID (see `telemetry.md` filter key table) |
| Granularity | `HOURLY` for usage signals; `MONTHLY` for business metrics |

**Filter key syntax:** `custom:Bedrock Telemetry Target` (display name), not
`User:Defined:BedrockTelemetryTarget` (YAML ID). Never mix these. See `telemetry.md`.

### Step 3 — Collector

Copy `onboarding/templates/collector.py.tmpl` into the change sub-folder. Fill in:

```
STREAM_NAME              = "<stream name from step 2>"
TARGET_DIMENSION_DISPLAY_NAME = "<Name: field of hidden dim>"
POOL_ELEMENTS            = ["<pool element name>"]
GRANULARITY              = "HOURLY"  # or MONTHLY for business metrics
```

Implement `collect_usage()` to return `{element_name: usage_value}` for the window.
Values are proportions — raw counts are fine; CloudZero normalizes within each window.
Element name keys must **exactly match** (case-sensitive) the target dimension's elements.

### Step 4 — Validate before first send

```bash
python3 collector.py --dry-run > payload.json
python3 costformation-brain/validator/telemetry_check.py payload.json \
    --costformation <costformation-file> \
    --target-dimension <TargetDimensionId>
```

Exit codes: 0 = OK, 1 = errors, 2 = usage error. Fix **all ERRORs** before proceeding.
Common errors: non-hourly-aligned timestamps (seconds/minutes not zero), `value` is a
number instead of a string, filter key using CostFormation source syntax instead of
telemetry display-name syntax, `element_name` case mismatch.

### Step 5 — Customer deploys; record waiting-external

Agree on a deploy schedule matching granularity (hourly cron for `HOURLY`, daily for
`DAILY`, first-of-month for `MONTHLY`). Record in the state file:

```yaml
per-dimension:
  Environment:
    status: waiting-external
    stream: bedrock-tokens-by-env-v1
    collector-deployed: <ISO date>
    verify-after: <deploy date + 2 days>
```

Run `python3 costformation-brain/validator/lint.py --check-integrity` after writing.

### Step 6 — Verify on resume

On the session after `verify-after`, the session-start wait check surfaces this entry.
When the customer confirms they're ready to continue:

1. Query the stream via MCP to confirm records are landing with the expected element
   names and proportions.
2. Check for gaps (missing windows produce `DefaultValue` fallback in allocations).
3. Confirm proportions look sane given what the customer knows about usage distribution.

If the stream looks wrong, fix the collector and re-send before proceeding. Do not build
the allocation dimension against bad telemetry — see `telemetry.md` investigation methodology.

### Step 7 — Write allocation and combined view dimensions

See STEPs 2–3 in `examples/patterns/allocation-telemetry-basic.yaml`.

**`AllocateByStreams` takes NO `SpendToAllocate`** — filtering happens entirely via the
stream's filter keys (set in step 2). Adding `SpendToAllocate` to an `AllocateByStreams`
dimension is an error. Scope is controlled by what the telemetry records' `filter` covers.

The hidden allocation dimension (`Type: Allocation`, `Hide: true`, `AllocateByStreams`
with the stream name) splits shared costs proportionally. The visible combined dimension
uses `GroupBy` with `CoalesceSources: true` to merge allocated shared costs with direct
costs — allocation output takes priority in the coalesce order so shared costs are not
double-counted.

### Step 8 — Validate and record exit checks

```bash
python3 costformation-brain/validator/lint.py <costformation-file>
python3 costformation-brain/validator/lint.py --check-integrity
```

Fix all ERRORs. Flip per-dimension status to `complete` and record exit-checks (see exit
criteria below). Update the shared-spend matrix in the state file.

---

## Human Questions

Only ask what the data cannot answer. In order:

1. **Which rung?** Present the agent's recommendation with the rationale (bucket size,
   available signals found in the data). The customer confirms or selects a different rung.
2. **Signal availability** (rungs 2–3): work DOWN the interview guide — ask about the
   ideal signal first, fall back to the proxy only if the ideal is unavailable.
3. **Derivation mappings** (if reusing an existing stream): ask for the tenant-to-product
   or tenant-to-team mapping CSV or confirm an existing one in `my-org/context.md`.
4. **Deploy schedule ownership**: who will run the collector and when? Agree on the
   schedule before writing `verify-after`.

Ask one at a time. Offer concrete candidates drawn from the data rather than open-ended
prompts: "I see your Bedrock spend runs ~$31k/mo. Do you have token counts per environment
in your API gateway logs?"

---

## Deliverables

Record all paths in `onboarding-state.yaml` under `artifacts`.

- `<change-folder>/<dimension-id>_<date>.yaml` — new/modified dimension YAML (target,
  allocation, combined view), clean and copy-paste ready
- `<change-folder>/<dimension-id>_<date>_comments.md` — what it does, paste location,
  dependencies, testing recommendations
- `<change-folder>/collector.py` — customized collector (rungs 2–3 only)
- Stream spec (record in comments file and state file `stream:` field)

---

## Exit Criteria and Recording Rule

Before flipping per-dimension status to `complete`, record all checks in the state file:

```yaml
per-dimension:
  Environment:
    status: complete
    method: telemetry-tokens-by-env
    exit-checks:
      - check: lint.py passes on all new dimensions without ERROR
        result: pass
        date: <ISO date>
      - check: allocation dimension visible and proportions verified via MCP
        result: pass
        date: <ISO date>
      - check: combined view confirmed in CloudZero UI
        result: pass
        date: <ISO date>
      - check: shared-spend matrix updated in state file
        result: pass
        date: <ISO date>
```

Run `python3 costformation-brain/validator/lint.py --check-integrity` after writing. Fix
ERRORs immediately.

The phase-level `allocation.status` stays `in_progress` while any dimension remains. Flip
to `complete` (with phase-level exit-checks) only when all per-dimension loops are done or
deliberately skipped.

---

## Worked Example — Bedrock Split by Tokens per Environment

**Setup:** Phase 3 matrix shows Bedrock at ~$31k/mo, unallocated under the Environment
lens. The matrix also shows Production, Staging, and Development as the Environment elements.

**Matrix finding:**

| Shared bucket | $/mo | Environment |
|---|---|---|
| Amazon Bedrock | 31,000 | unallocated |

**Step 1 — Rung choice**

$31k/mo warrants fidelity. Agent recommends rung 3 (service usage telemetry). Two human
questions asked:

> "Your Bedrock spend is $31k/mo and currently unallocated under Environment. For a split
> this size I'd recommend using actual token counts. Do you have per-environment token
> data in your API gateway logs or in the Bedrock usage metrics in CloudWatch?"

Customer: "Yes, we log tokens per environment tag in our gateway."

> "Great. Does that log include both input and output tokens, or just one?"

Customer: "Both — we sum them per request."

**Step 2 — Stream spec**

| Field | Value |
|---|---|
| Stream name | `bedrock-tokens-by-env-v1` |
| Target dimension ID | `BedrockTelemetryTarget` |
| Target dimension Name | `Bedrock Telemetry Target` |
| Pool element | `Bedrock` |
| Allocation targets | `Production`, `Staging`, `Development` |
| Filter key | `custom:Bedrock Telemetry Target` |
| Granularity | `HOURLY` |

**Step 3 — Hidden target dimension (STEP 1 in allocation-telemetry-basic.yaml pattern)**

```yaml
BedrockTelemetryTarget:
  Name: Bedrock Telemetry Target
  Hide: true
  Rules:
    - Type: Group
      Name: Production
      Conditions:
        - Source: Tag:environment
          Equals: [production, prod]
    - Type: Group
      Name: Staging
      Conditions:
        - Source: Tag:environment
          Equals: [staging, stage]
    - Type: Group
      Name: Development
      Conditions:
        - Source: Tag:environment
          Equals: [development, dev]
    - Type: Group
      Name: Bedrock
      Conditions:
        - Source: Service
          Equals: AmazonBedrock
```

**Step 4 — Collector CONFIG values**

```python
STREAM_NAME = "bedrock-tokens-by-env-v1"
TARGET_DIMENSION_DISPLAY_NAME = "Bedrock Telemetry Target"
POOL_ELEMENTS = ["Bedrock"]
GRANULARITY = "HOURLY"
```

`collect_usage()` queries the gateway log store for the previous hour, sums
`input_tokens + output_tokens` grouped by `environment` tag value, and returns a dict with
keys matching exactly `Production`, `Staging`, `Development`.

**Step 5 — Sample payload (API POST body shape)**

Adapt from the `allocation-telemetry-basic.yaml` pattern comment block, replacing element
names with the Environment example:

```json
{
  "records": [
    {
      "timestamp": "2026-06-01T00:00:00Z",
      "granularity": "HOURLY",
      "filter": {"custom:Bedrock Telemetry Target": ["Bedrock"]},
      "element_name": "Production",
      "value": "182400"
    },
    {
      "timestamp": "2026-06-01T00:00:00Z",
      "granularity": "HOURLY",
      "filter": {"custom:Bedrock Telemetry Target": ["Bedrock"]},
      "element_name": "Staging",
      "value": "34100"
    },
    {
      "timestamp": "2026-06-01T00:00:00Z",
      "granularity": "HOURLY",
      "filter": {"custom:Bedrock Telemetry Target": ["Bedrock"]},
      "element_name": "Development",
      "value": "13500"
    }
  ]
}
```

**Step 6 — Validation command**

```bash
python3 collector.py --dry-run > payload.json
python3 costformation-brain/validator/telemetry_check.py payload.json \
    --costformation my-costformation.cz.yaml \
    --target-dimension BedrockTelemetryTarget
# Expected: OK: 3 records, 0 errors, 0 warnings
```

**Step 7 — waiting-external state snippet**

```yaml
per-dimension:
  Environment:
    status: waiting-external
    stream: bedrock-tokens-by-env-v1
    collector-deployed: 2026-06-14
    verify-after: 2026-06-16
```

**Step 8 — Final dimensions (after stream verified)**

Follow STEPs 2–3 in `examples/patterns/allocation-telemetry-basic.yaml`. The hidden
`AllocateByStreams` dimension references `bedrock-tokens-by-env-v1`. The visible combined
dimension (`GroupBy`, `CoalesceSources: true`) merges it with direct Environment spend.
`AllocateByStreams` takes no `SpendToAllocate` — the stream's filter (`custom:Bedrock
Telemetry Target` → `Bedrock`) scopes the allocation.

---

## Go Deeper

- `telemetry.md` — record shape, filter key syntax, two-stage deploy, investigation
  methodology, replace vs delete-then-replace
- `allocation-design.md` — expansion factor, `SpendToAllocate` scoping rules, overlap
  investigation, hidden-dimension sprawl anti-pattern
- https://docs.cloudzero.com/docs/telemetry-streams — stream management
- https://docs.cloudzero.com/docs/send-via-api — API reference for posting records
- https://docs.cloudzero.com/reference/allocation-telemetry-api-1 — full telemetry API
  reference
