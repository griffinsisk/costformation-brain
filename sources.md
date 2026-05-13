# Sources Reference

## Source Syntax

Some sources require a prefix, others are bare. Use the wrong form and the definition will fail.

**Prefixed sources** — always use the full prefix:
```yaml
Source: CZ:Defined:<DimensionId>      # CloudZero built-in dimensions
Source: User:Defined:<DimensionId>    # Your own custom dimensions
Source: Tag:<TagName>                 # AWS/Azure/GCP tags
Source: K8s:Label:<LabelName>         # Kubernetes labels
Source: K8s:Namespace                 # Kubernetes namespace
Source: K8s:Cluster                   # Kubernetes cluster
Source: K8s:Workload                  # Kubernetes workload
```

**Bare sources** — no prefix, used as-is:
```yaml
Source: Account          # AWS account ID, Azure subscription, GCP project
Source: Service          # Cloud service code
Source: Region           # Cloud region
Source: Resource         # CloudZero Resource Name (CZRN)
Source: UsageFamily      # Usage family
Source: CloudProvider    # AWS, GCP, Azure, etc.
Source: UsageType        # Usage type
Source: Operation        # Cloud operation
```

> Writing `Source: CZ:Defined:Account` is **wrong** — `Account` is a bare source. Writing `Source: Environment` is also wrong — custom dimensions need `User:Defined:Environment`.

## Complete Source Reference

Canonical list of all CloudZero dimensions with their CostFormation source syntax, API reference, and telemetry filter key.

### Core Billing Dimensions

| UI Name | CostFormation Source | Telemetry Filter Key | Notes |
|---|---|---|---|
| Account | `Account` | `accounts` | AWS account ID, Azure subscription, GCP project |
| Service | `Service` | `services` | Cloud service codes |
| Region | `Region` | `region` | |
| Usage Family | `UsageFamily` | `product_family` | |
| Usage Type | `UsageType` | N/A | Usage details of billing line item |
| Cloud Provider | `CloudProvider` | `cloud_provider` | AWS, GCP, Azure, etc. |
| Operation | `Operation` | N/A | Specific cloud operation |
| Product Family | `ProductFamily` | N/A | E.g. Compute Instance, NAT Gateway |
| Pricing Term | `PricingTerm` | N/A | On-demand, reserved, spot |
| Line Item Type | `LineItemType` | N/A | Type of billing charge |
| Payer Account | `PayerAccount` | N/A | Management/payer account |
| Description | `Description` | N/A | Detailed billing text field |
| Usage Day | `UsageDay` | N/A | ISO-formatted date for line item |
| Transfer Type | `TransferType` | N/A | Data transfer type |
| Request Type | `RequestType` | N/A | E.g. CloudFront request types |
| Invoice ID | `InvoiceID` | N/A | |
| Billing Connection ID | `BillingConnectionID` | N/A | Links charges to billing connection |
| Committed Use Subscription | `CommittedUseSubscription` | N/A | RI/Savings Plan details |
| Pricing Unit | `PricingUnit` | N/A | Unit of measurement |
| Pricing Units | `PricingUnits` | N/A | Unit of measure for pricing (GB, hours) |

### CloudZero Built-In Dimensions (`CZ:Defined:`)

| UI Name | CostFormation Source | Telemetry Filter Key | Notes |
|---|---|---|---|
| Resource Summary | `CZ:Defined:ResourceSummaryDisplay` | `custom:Resource Summary Display` | **Preferred for resource matching** — groups related resources, low cardinality |
| Resource Summary ID | `CZ:Defined:ResourceSummaryID` | N/A | Grouped resources with CZRNs |
| Resource Display | `CZ:Defined:ResourceDisplay` | N/A | Native resource IDs (not CZRNs) |
| Resource (name only) | `CZ:Defined:ResourceNameOnly` | N/A | Just the resource name without account/region context |
| Service Display | `CZ:Defined:ServiceDisplay` | N/A | Service display values |
| Service Detail | `CZ:Defined:ServiceDetail` | `custom:Service Detail` | More granular than Service |
| Service Category | `CZ:Defined:Category` | `custom:Category` | E.g. "Non-Usage: SavingsPlanRecurringFee" |
| Elasticity | `CZ:Defined:Elasticity` | N/A | Storage vs Variable Costs |
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

Tag keys are **case-sensitive**. Always use `Lower` transforms when matching user-applied tags.

### Kubernetes Dimensions

| UI Name | CostFormation Source | API Reference | Telemetry Filter Key |
|---|---|---|---|
| K8s Cluster | `K8s:Cluster` | `K8s:Cluster:<ClusterName>` | `k8s_cluster:<ClusterName>` |
| K8s Namespace | `K8s:Namespace` | `K8s:Namespace:<NamespaceName>` | `k8s_namespace:<NamespaceName>` |
| K8s Workload | `K8s:Workload` | `K8s:Workload:<WorkloadName>` | `k8s_workload:<WorkloadName>` |
| K8s Label | `K8s:Label:<LabelName>` | `K8s:Label:<LabelName>` | `k8s_label:<LabelName>` |
| K8s Pod | `K8s:Pod` | N/A | N/A |

Note: API references for K8s dimensions require the specific name (e.g. `K8s:Namespace:production`). CostFormation sources do not — `K8s:Namespace` matches across all namespaces.

**K8s Label format variants:**
```yaml
# Pod labels (most common)
K8s:Label:<label-key>

# Non-pod resource labels (e.g. node, service)
K8s:Label:<resource-type>:<label-key>

# Pod annotations
K8s:Label:annotation:<label-key>

# Non-pod resource annotations
K8s:Label:<resource-type>:annotation:<label-key>
```

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
