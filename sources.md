# Sources Reference

## Prefix Syntax — Always Required

```yaml
# CloudZero built-in dimensions:
Source: CZ:Defined:<DimensionId>

# User-defined (your own) dimensions:
Source: User:Defined:<DimensionId>

# Tag dimensions:
Source: Tag:<TagName>
```

> ⚠️ Writing bare `Source: Environment` (no prefix) is **invalid** and will fail. Always use the full prefixed form.

## Commonly Used Source IDs

| Source ID | What It Is | Notes |
|---|---|---|
| `Account` | AWS account ID or Azure subscription | Core billing dimension |
| `Service` | Cloud service name (e.g. `AmazonEC2`) | Case-sensitive |
| `ServiceDetail` | More granular service breakdown | |
| `Region` | Cloud region (e.g. `us-east-1`) | |
| `UsageType` | Billing usage type string | |
| `ResourceId` | Raw resource ID | **Avoid** — high cardinality, expensive in Snowflake |
| `CZ:Defined:ResourceSummaryDisplay` | CloudZero-normalized resource ID | **Preferred for resource matching** |
| `Tag:<TagName>` | Any AWS/Azure tag | Case-sensitive tag key |
| `Kubernetes:Namespace` | K8s namespace | Requires K8s integration |
| `Kubernetes:Label:<LabelKey>` | K8s pod/workload label | Requires K8s integration |

## Source Inheritance vs. Override

When a rule specifies `Source:`, it **overrides all source properties** inherited from the dimension — including transforms and coalesce settings. If you only want to change the source for one condition, set it on the condition, not the rule.

## List Available Sources (API)

```
GET https://api.cloudzero.com/v2/billing/dimensions
```

Returns all Core + Custom Dimension IDs usable in `Source:` fields for your org.
