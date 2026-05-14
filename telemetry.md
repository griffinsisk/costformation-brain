# Telemetry API & Stream Design

Telemetry powers `AllocateByStreams` dimensions. You send usage signals to CloudZero; it uses them to split shared costs proportionally.

## How the Pipeline Works

1. **Build a target dimension** — a standard dimension (or group within one) that defines the elements you want to allocate costs to. E.g., an Environment dimension with Production, Staging, Development elements. This must exist first.
2. **Send telemetry records** — usage metrics (API calls, bytes, tokens, etc.) that reference the target dimension's elements via `element_name`. The `filter` narrows which charges each record applies to. The proportions tell CloudZero how to split.
3. **This creates a stream** — the stream name in the API URL becomes a source you reference in CostFormation.
4. **Build an allocation dimension** — uses `AllocateByStreams` with your stream. It splits shared costs back to the target elements proportionally based on the telemetry signal.
5. **Combine with a final dimension** — use `GroupBy Source: User:Defined:<AllocationDim>` to merge the allocated shared costs with direct costs into one unified view.

Example: Bedrock is shared across environments. You send token usage per environment as telemetry → the stream splits Bedrock costs proportionally → a final Environment Allocated dimension shows each environment's direct costs plus its share of Bedrock.

## Endpoint

```
POST https://api.cloudzero.com/v1/telemetry/{stream_name}
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

`stream_name` in the URL must **exactly match** the stream name in your CostFormation YAML.

## Record Shape

```json
{
  "records": [
    {
      "timestamp": "2024-01-15T14:00:00Z",
      "granularity": "DAILY",
      "filter": {
        "custom:Shared RDS": ["Shared Data Lake"]
      },
      "element_name": "Email",
      "value": "100045"
    }
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `timestamp` | Yes | ISO 8601 format, hourly-aligned UTC |
| `granularity` | Yes | `HOURLY`, `DAILY`, or `MONTHLY` |
| `filter` | Yes | Telemetry filter keys (see `sources.md`) mapping dimension names to element arrays |
| `element_name` | Yes | The target element in the allocation dimension — must exactly match an element name |
| `value` | Yes | The usage metric (string-encoded number). CloudZero normalizes proportionally within each time window |

## Rules for Telemetry Records

1. **Timestamps must be hourly-aligned UTC** — minutes and seconds must be `00:00`. Example: `2024-01-15T14:00:00Z` ✅ — `2024-01-15T14:23:11Z` ❌
2. **Default to `HOURLY` granularity** — matches CloudZero's billing reprocessing cadence
3. **`element_name` must exactly match element names** in your allocation dimension — case-sensitive
4. **`filter` uses telemetry filter keys** (see `sources.md`) — NOT CostFormation source syntax. E.g., `"custom:Environment"` not `"User:Defined:Environment"`
5. **Send proportions, not absolute values** — CloudZero normalizes within each time window. `{a:100, b:200}` is equivalent to `{a:1, b:2}`
5. **Telemetry must arrive before nightly reprocessing** — aim to send within 2 hours of the period it covers. Late data triggers expensive retroactive reprocessing
6. **Don't backfill more than 90 days** unless on Enterprise tier
7. **Missing windows** — if no telemetry exists for a time window, costs fall to `DefaultValue`. Ensure continuous coverage

## Stream Design Guidelines

- **Name streams descriptively**: `customer-api-requests` not `stream1`
- **Version your stream names** (e.g. `-v2` suffix) — telemetry is hard to change once sent, but dimensions are easy to modify
- **Stream names are global per org** — two dimensions can share a stream if they use the same signal
- **Design stream priority carefully**: put the most precise signal first, broader fallbacks last
- **Don't send redundant streams** — if two streams cover the same resources for the same period, the lower-priority one is stored but ignored

## Dedicated Telemetry Target Dimensions

**Key principle**: telemetry is difficult to change once sent, but dimensions are easy to modify. Instead of filtering streams by raw tags, create a dedicated hidden "target" dimension and reference it in your telemetry records.

```yaml
# GOOD — dedicated telemetry target dimension
ApplicationTelemetryTarget:
  Name: Application Telemetry Target
  Hide: true
  Rules:
    - Type: Group
      Name: WebApp
      Conditions:
        - Source: Tag:application
          Equals: [web-app, webapp]
    - Type: Group
      Name: API
      Conditions:
        - Source: Tag:application
          Equals: [api, backend-api]
```

Telemetry records reference the **dimension element**, not the raw tag:

```json
{
  "timestamp": "2024-01-25T00:00:00Z",
  "granularity": "DAILY",
  "filter": {
    "custom:ApplicationTelemetryTarget": ["WebApp"],
    "tag:environment": ["prod"]
  },
  "element_name": "team-alpha",
  "value": "250000000"
}
```

This way, if tag values change (e.g. `web-app` → `frontend`), you update the dimension rule — not every telemetry sender.

```yaml
# BAD — referencing tags directly in telemetry records
# If tag values change, every telemetry sender must be updated
{
  "filter": {
    "tag:application": ["web-app", "api"]
  },
  "element_name": "team-alpha",
  "value": "250000000"
}
```

## Telemetry Filter Keys

When constructing telemetry record `filter` objects, use these keys to reference CloudZero dimensions. The filter key format differs from CostFormation source syntax.

| Dimension Type | CostFormation Source | Telemetry Filter Key |
|---|---|---|
| Account | `Account` | `accounts` |
| Service | `Service` | `services` |
| Region | `Region` | `region` |
| Cloud Provider | `CloudProvider` | `cloud_provider` |
| Usage Family | `UsageFamily` | `product_family` |
| Tags | `Tag:<TagName>` | `tag:<TagName>` |
| K8s Cluster | `K8s:Cluster` | `k8s_cluster:<ClusterName>` |
| K8s Namespace | `K8s:Namespace` | `k8s_namespace:<NamespaceName>` |
| K8s Workload | `K8s:Workload` | `k8s_workload:<WorkloadName>` |
| K8s Label | `K8s:Label:<LabelName>` | `k8s_label:<LabelName>` |
| Custom dimension | `User:Defined:<DimId>` | `custom:<Dimension UI Name>` |
| CZ built-in | `CZ:Defined:<DimId>` | `custom:<Dimension UI Name>` |

Note: the telemetry filter key for custom and CZ built-in dimensions uses the **UI display name** (the `Name:` field), not the DimensionId. See `sources.md` for the complete mapping.

Example filter using multiple dimension types:
```json
{
  "filter": {
    "custom:ApplicationTelemetryTarget": ["WebApp"],
    "tag:environment": ["prod"],
    "accounts": ["123456789012"]
  }
}
```

## Common Telemetry Sources

| Use Case | Signal to Send | Typical Source |
|---|---|---|
| Cost per Customer | Request count, active seats | App metrics, Datadog, CloudWatch |
| Cost per Feature | CPU/memory by workload | Kubernetes metrics |
| Cost per Team | Resource ownership ratio | CMDB, tags, Terraform state |

## Python Example

```python
import requests
from datetime import datetime, timezone

records = [
    {
        "timestamp": hour_utc.strftime("%Y-%m-%dT%H:00:00Z"),
        "granularity": "HOURLY",
        "filter": {"custom:Customer": [customer_id]},
        "element_name": customer_id,
        "value": request_count,
    }
    for customer_id, request_count in hourly_counts.items()
]

requests.post(
    "https://api.cloudzero.com/v1/telemetry/customer-api-requests",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"records": records}
)
```

---

## Telemetry Key Reference

Record `filter` keys and query `group_by` keys use **different naming conventions**. Do not mix them.

### Record Filter Keys

Used in CSV columns and API `filter` objects when sending telemetry records.

| CostFormation Source | Telemetry Record Filter Key |
|---|---|
| `Account` | `accounts` |
| `Service` | `services` |
| `Region` | `region` |
| `CloudProvider` | `cloud_provider` |
| `UsageFamily` | `product_family` |
| `CZ:Defined:ResourceSummaryDisplay` | `custom:Resource Summary Display` |
| `CZ:Defined:ResourceType` | `custom:Resource Type` |
| `CZ:Defined:Category` | `custom:Category` |
| `CZ:Defined:GenAI_Model` | `custom:GenAI Model` |
| `CZ:Defined:GenAI_Platform` | `custom:GenAI Platform` |
| `CZ:Defined:GenAI_TokenType` | `custom:GenAI Token Type` |
| `CZ:Defined:GenAI_Model_Family` | `custom:GenAI Model Family` |
| `CZ:Defined:InstanceType` | `custom:Instance Type` |
| `CZ:Defined:PaymentOption` | `custom:Payment Option` |
| `CZ:Defined:ServiceDetail` | `custom:Service Detail` |
| `CZ:Defined:BillingLineItem` | `custom:Billing Line Item` |
| `CZ:Defined:NetworkCategory` | `custom:Networking Category` |
| `CZ:Defined:NetworkSubCategory` | `custom:Networking Sub-Category` |
| `CZ:Defined:TaggableVsUntaggable` | `custom:Taggable vs. Untaggable` |
| `User:Defined:<DimId>` | `custom:<Dimension Display Name>` |
| `Tag:<TagName>` | `tag:<TagName>` |
| `K8s:Namespace` | `k8s_namespace:Name` |
| `K8s:Cluster` | `k8s_cluster:Name` |
| `K8s:Label:<LabelName>` | `k8s_label:<LabelName>` |
| `K8s:Workload` | `k8s_workload:Name` |
| `Resource` (CZRN) | Not applicable |
| `CZ:Defined:ResourceNameOnly` | Not applicable |

For `User:Defined:<DimId>`, the filter key uses the dimension's UI display name (the `Name:` field in CostFormation), not the DimensionId.

### Query group_by Keys

Used in telemetry query API requests (`group_by` parameter). These use the API Reference format — the same source identifiers used in CostFormation — plus `element_name` for grouping by telemetry element.

| What to group by | group_by Key |
|---|---|
| Account | `Account` |
| Service | `Service` |
| Region | `Region` |
| Cloud Provider | `CloudProvider` |
| Usage Family | `UsageFamily` |
| Tag | `Tag:<TagName>` |
| CZ built-in dimension | `CZ:Defined:<DimId>` |
| Custom dimension | `User:Defined:<DimId>` |
| K8s Namespace | `K8s:Namespace` |
| K8s Cluster | `K8s:Cluster` |
| K8s Workload | `K8s:Workload` |
| K8s Label | `K8s:Label:<LabelName>` |
| Telemetry element | `element_name` |

---

## UCA CLI Quirks

When using the CloudZero UCA (Usage and Cost Allocation) CLI to upload telemetry, watch for these known issues:

1. **`$ENV_VAR` is not resolved** — the UCA CLI does not expand shell environment variables in config files or arguments. Substitute values explicitly before passing them, or export them into the invocation context with a wrapper script. Using `$API_KEY` or `${STREAM_NAME}` literally in a YAML config will be sent as-is and fail silently.

2. **Monthly granularity is omitted from some CLI docs** — the CLI supports `HOURLY`, `DAILY`, and `MONTHLY` granularities, but older documentation examples only show `HOURLY` and `DAILY`. If you need monthly signals (e.g. amortized commitments), pass `granularity: MONTHLY` explicitly. Missing this causes the API to reject records with an invalid granularity error.

3. **CZ system dimension prefix confusion** — the CLI documentation sometimes refers to CZ built-in dimensions without their `CZ:Defined:` prefix. When specifying filter keys or group_by values in CLI config, always use the full prefix form (`CZ:Defined:ResourceSummaryDisplay`, etc.) for CostFormation references. The telemetry record filter keys use `custom:` — not `CZ:Defined:` — so the two representations must never be mixed in the same file.

---

## Replace vs Delete-Then-Replace

Choosing between `/replace` and delete-then-replace depends on who controls the record keys.

**Use `/replace` (safe, atomic) when:** CloudZero generates or controls the record keys — machine-assigned IDs, system timestamps. The API guarantees idempotent replacement.

**Use delete-then-replace when:** Users supply string keys (element names, custom identifiers). User-supplied keys can drift: elements get renamed, removed, or re-keyed. A plain `/replace` in this case silently accumulates stale records alongside new ones.

**Decision flow:**

1. **Delete** — call the stream delete endpoint to remove all records for the target window or element.
2. **Validate empty** — query the stream and confirm zero records remain for that scope. Do not proceed if records are still present; the delete may be async.
3. **Upload** — send the fresh records via the telemetry API.

Never delete without confirming emptiness before re-uploading. A partial delete followed by a full upload produces double-counted data in that window.

---

## UI Upload Caveat

For streams with **monthly granularity**, prefer the API `/replace` endpoint over the UI CSV upload tool.

The UI uploader is designed for hourly and daily records. Monthly-keyed records can be accepted by the UI but may be misaligned during ingestion — the UI normalizes timestamps in ways that shift monthly records to unexpected billing windows. Use the API directly for monthly signals to guarantee the timestamp and granularity are preserved exactly as submitted.

---

## Two-Stage Deploy for New Allocation Chains

When introducing a brand-new telemetry-backed allocation dimension, deploy in two stages:

**Stage 1 — Deploy dimensions and create streams**
1. Deploy the target dimension (e.g. Environment) and any other prerequisite dimensions referenced in telemetry filters.
2. Create the telemetry stream and begin sending records.
3. Wait approximately 45 minutes for CloudZero to ingest and index the stream data.

**Stage 2 — Deploy allocation dimension**
4. Once the stream has data, deploy the `AllocateByStreams` dimension that references it.

Never create a stream and immediately deploy the allocation dimension in the same operation. An allocation dimension referencing an empty stream will assign 100% of costs to `DefaultValue` (or "Not in Dimension") for every historical window until data arrives. Retroactive reprocessing is expensive and slow.

Also: never create a stream with an empty filter `{}`. An unfiltered stream matches all charges across the entire org and will produce nonsensical proportions. Always include at least one filter key that scopes the stream to the relevant cost pool.

---

## Investigation Methodology

When a telemetry-backed allocation dimension produces unexpected results, start with the telemetry data itself — not the CostFormation YAML.

**Step 1: Query the telemetry stream directly**

Use the telemetry query API with ALL key dimensions in `group_by`:

```json
{
  "stream_name": "your-stream",
  "group_by": ["element_name", "Account", "Service", "User:Defined:YourTargetDim"],
  "granularity": "DAILY",
  "start": "2024-01-01T00:00:00Z",
  "end": "2024-01-08T00:00:00Z"
}
```

Look for: missing elements, unexpected element names (case mismatch), gaps in coverage, elements with zero signal that should have signal.

**Step 2: Fix telemetry at the source**

If the telemetry records are wrong — wrong element names, missing time windows, bad filter scope — fix them in the telemetry pipeline. Do not work around bad telemetry by adding compensating conditions in CostFormation. A CostFormation workaround makes the bad telemetry invisible, not correct, and compounds future debugging.

Correct the records, delete the affected window, re-upload, and wait for reprocessing before re-validating.

---

## Validate with the Customer's Cost Metric

Before finalizing any allocation dimension, confirm which cost metric the customer's CloudZero views are configured to use:

- `real_cost` — actual billed charges, no amortization
- `amortized_cost` — upfront commitment costs spread over the commitment period
- `invoiced_amortized_cost` — amortized view aligned to invoice periods

Query telemetry results and allocation outputs using the **same metric** the customer uses in their dashboards. Mismatched metrics produce numbers that look wrong even when the allocation logic is correct.

**Cross-check with a second metric when results look off.** If `amortized_cost` allocation looks suspicious, run the same query with `real_cost`. A large divergence between the two usually indicates commitment purchases (Reserved Instances, Savings Plans) are landing in unexpected elements — the allocation dimension is capturing them correctly per the telemetry signal, but the customer's expectations were set against a different cost view.
```
