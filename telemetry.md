# Telemetry API & Stream Design

Telemetry powers `AllocateByStreams` dimensions. You send usage signals to CloudZero; it uses them to split shared costs proportionally.

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
      "filter": {
        "element_tag": "acme-corp"
      },
      "value": 142.5,
      "timestamp": "2024-01-15T14:00:00Z",
      "granularity": "HOURLY"
    }
  ]
}
```

## Rules for Telemetry Records

1. **Timestamps must be hourly-aligned UTC** — minutes and seconds must be `00:00`. Example: `2024-01-15T14:00:00Z` ✅ — `2024-01-15T14:23:11Z` ❌
2. **Default to `HOURLY` granularity** — matches CloudZero's billing reprocessing cadence
3. **Element tags must exactly match element names** in your dimension — case-sensitive
4. **Send proportions, not absolute values** — CloudZero normalizes within each time window. `{a:100, b:200}` is equivalent to `{a:1, b:2}`
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
  "element-name": "team-alpha",
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
  "element-name": "team-alpha",
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
        "filter": {"element_tag": customer_id},
        "value": request_count,
        "timestamp": hour_utc.strftime("%Y-%m-%dT%H:00:00Z"),
        "granularity": "HOURLY"
    }
    for customer_id, request_count in hourly_counts.items()
]

requests.post(
    "https://api.cloudzero.com/v1/telemetry/customer-api-requests",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"records": records}
)
```
