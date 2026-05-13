# Sources Reference

> Complete dimension mapping sourced from the canonical *CZ Dimension Reference* spreadsheet. Original preserved in `reference/CZ Dimension Reference.csv`.

## Prefix Syntax — Always Required

```yaml
# CloudZero built-in dimensions:
Source: CZ:Defined:<DimensionId>

# User-defined (your own) dimensions:
Source: User:Defined:<DimensionId>

# Tag dimensions:
Source: Tag:<TagName>

# Kubernetes dimensions:
Source: K8s:Label:<LabelName>
Source: K8s:Namespace
Source: K8s:Cluster
Source: K8s:Workload
```

> Writing bare `Source: Environment` (no prefix) is **invalid** and will fail. Always use the full prefixed form.

## Complete Source Reference

Canonical list of all CloudZero dimensions with their CostFormation source syntax, API reference, and telemetry filter key.

### Core Billing Dimensions

| UI Name | CostFormation Source | API Reference | Telemetry Filter Key |
|---|---|---|---|
| Account | `Account` | `Account` | `accounts` |
| Service | `Service` | `Service` | `services` |
| Region | `Region` | `Region` | `region` |
| Usage Family | `UsageFamily` | `UsageFamily` | `product_family` |
| Cloud Provider | `CloudProvider` | `CloudProvider` | `cloud_provider` |

### CloudZero Built-In Dimensions (`CZ:Defined:`)

| UI Name | CostFormation Source | Telemetry Filter Key | Notes |
|---|---|---|---|
| Resource Summary | `CZ:Defined:ResourceSummaryDisplay` | `custom:Resource Summary Display` | **Preferred for resource matching** — groups related resources, low cardinality |
| Resource (name only) | `CZ:Defined:ResourceNameOnly` | N/A | Just the resource name without account/region context |
| Service Detail | `CZ:Defined:ServiceDetail` | `custom:Service Detail` | More granular than Service |
| Service Category | `CZ:Defined:Category` | `custom:Category` | E.g. "Non-Usage: SavingsPlanRecurringFee" |
| Instance Type | `CZ:Defined:InstanceType` | `custom:Instance Type` | EC2/RDS instance family and size |
| Resource Type | `CZ:Defined:ResourceType` | `custom:Resource Type` | |
| Billing Line Item | `CZ:Defined:BillingLineItem` | `custom:Billing Line Item` | |
| Payment Option | `CZ:Defined:PaymentOption` | `custom:Payment Option` | On-Demand, Reserved, Savings Plan, Spot |
| Networking Category | `CZ:Defined:NetworkCategory` | `custom:Networking Category` | |
| Networking Sub-Category | `CZ:Defined:NetworkSubCategory` | `custom:Netowrking Sub-Category` | Note: telemetry key has a typo — use as-is |
| Taggable vs. Untaggable | `CZ:Defined:TaggableVsUntaggable` | `custom:Taggable vs. Untaggable` | |

### GenAI Dimensions (`CZ:Defined:`)

| UI Name | CostFormation Source | Telemetry Filter Key |
|---|---|---|
| GenAI Model | `CZ:Defined:GenAI_Model` | `custom:GenAI Model` |
| GenAI Model Family | `CZ:Defined:GenAI_Model_Family` | `custom:GenAI Model Family` |
| GenAI Platform | `CZ:Defined:GenAI_Platform` | `custom:GenAI Platform` |
| GenAI Token Type | `CZ:Defined:GenAI_TokenType` | `custom:GenAI Token Type` |

### Tag Dimensions

```yaml
# CostFormation:
Source: Tag:<TagName>          # e.g. Tag:environment, Tag:team

# API reference (URL encoding required):
Tag:<TagName>

# Telemetry filter key:
tag:<TagName>                  # e.g. tag:environment
```

Tag keys are **case-sensitive**. Always use `Lowercase` transforms when matching user-applied tags.

### Kubernetes Dimensions

| UI Name | CostFormation Source | API Reference | Telemetry Filter Key |
|---|---|---|---|
| K8s Cluster | `K8s:Cluster` | `K8s:Cluster:<ClusterName>` | `k8s_cluster:<ClusterName>` |
| K8s Namespace | `K8s:Namespace` | `K8s:Namespace:<NamespaceName>` | `k8s_namespace:<NamespaceName>` |
| K8s Workload | `K8s:Workload` | `K8s:Workload:<WorkloadName>` | `k8s_workload:<WorkloadName>` |
| K8s Label | `K8s:Label:<LabelName>` | `K8s:Label:<LabelName>` | `k8s_label:<LabelName>` |

Note: API references for K8s dimensions require the specific name (e.g. `K8s:Namespace:production`). CostFormation sources do not — `K8s:Namespace` matches across all namespaces.

### User-Defined Dimensions

```yaml
# CostFormation:
Source: User:Defined:<DimensionId>    # e.g. User:Defined:Environment

# API reference:
User:Defined:<DimensionId>

# Telemetry filter key:
custom:<Dimension Name In UI>         # e.g. custom:Environment
```

The CostFormation reference uses the **DimensionId** (YAML key). The telemetry filter key uses the **display Name** (the `Name:` field). These are often different.

### CZRN (CloudZero Resource Name)

| UI Name | CostFormation Source | Telemetry Filter Key |
|---|---|---|
| CloudZero Resource Name | `Resource` | N/A |

`Resource` is the raw CloudZero resource identifier. Use `CZ:Defined:ResourceSummaryDisplay` instead for matching — it's normalized and lower cardinality.

## Source Inheritance vs. Override

When a rule specifies `Source:`, it **overrides all source properties** inherited from the dimension — including transforms and coalesce settings. If you only want to change the source for one condition, set it on the condition, not the rule.

## List Available Sources (API)

```
GET https://api.cloudzero.com/v2/billing/dimensions
```

Returns all Core + Custom Dimension IDs usable in `Source:` fields for your org.
