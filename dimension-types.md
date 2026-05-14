# Dimension Types

## 1. Standard (Filter/GroupBy) Dimensions

Assigns each charge to exactly one element. Used for filtering and grouping in Explorer and Views.

Every rule must have `Type: Group` or `Type: GroupBy`.

```yaml
Dimensions:
  Environment:
    Name: Environment
    DefaultValue: Unknown    # omit unless you need a named catch-all — see performance-rules.md
    Rules:
      - Type: Group
        Name: Production
        Conditions:
          - Or:
            - Source: Account
              Equals:
                - "111111111111"
                - "222222222222"
            - Source: Tag:env
              Equals: production
      - Type: Group
        Name: Staging
        Conditions:
          - Source: Tag:env
            Equals: staging
```

## 2. Child Dimensions

Inherit structure from a parent dimension, adding transforms or overrides. Useful for deriving a coarser dimension from a finer one.

```yaml
Dimensions:
  Country:
    Name: Custom Country Dimension
    DefaultValue: global    # omit unless you need a named catch-all — see performance-rules.md
    Child: Region
    Rules:
      - Type: GroupBy
        Source: Region
        Transforms:
          - Type: Split
            Delimiter: "-"
            Index: 1    # extracts "us" from "us-east-1"
```

## 3. Allocation Dimensions

Splits shared costs proportionally across elements. Two subtypes:

### 3a. Rules-Based Allocation

Splits based on another dimension's element spend ratios. No telemetry required.

**AllocationMethod options:** `Proportional` (by spend ratio), `Even` (equal split), `Fixed` (fixed weight).

```yaml
Dimensions:
  SharedInfraByProduct:
    Type: Allocation
    Name: Shared Infra Allocated by Product
    AllocateByRules:
      AllocationMethod: Proportional
      SpendToAllocate:
        Source: User:Defined:SharedRDS
        Conditions:
          - Equals: Shared Data Lake
      AcrossElements:
        GroupBy:
          Source: User:Defined:Product
          Conditions:
            - Equals:
              - Product A
              - Product B
              - Product C
```

`AcrossElements` uses shorthand syntax: `GroupBy`, `Groups`, or `Rules` — not a bare `Source`.

### 3b. Telemetry-Based Allocation

Splits based on real usage signals sent via the Telemetry API. Most precise, but requires instrumentation. See `telemetry.md`.

```yaml
Dimensions:
  Customer:
    Type: Allocation
    Name: Cost per Customer
    AllocateByStreams:
      Streams:
        - customer-requests       # highest priority stream
        - customer-active-seats   # fallback
```

Streams are evaluated top-to-bottom. If multiple streams target the same resource for the same time window, the highest-priority stream wins.

### 3c. ForEachElementOf (Partitioned Allocation)

Partitions allocations by a parent dimension, **reducing** the expansion factor by limiting each allocation pass to only the elements present in that partition. Use low-to-medium cardinality dimensions as the partition key (Region, Account, Environment).

```yaml
Dimensions:
  SharedResourcesByTeam:
    Type: Allocation
    Name: Shared Resources by Team
    AllocateByRules:
      AllocationMethod: Proportional
      ForEachElementOf: Region
      SpendToAllocate:
        Conditions:
          - Source: User:Defined:AllocationTargetSpend
            Equals: Shared Resources
      AcrossElements:
        Rules:
          - Type: GroupBy
            Source: User:Defined:Team
```

See `allocation-design.md` for the full set of allocation design rules including the common "Spend to Allocate" dimension pattern, anti-overlap, and anti-layering.

### 3d. Rate-Based Telemetry Allocation

Applies a fixed rate multiplier to telemetry-based allocation. Unallocated portions go to a named default element.

```yaml
Dimensions:
  RatedAllocation:
    Type: Allocation
    AllocateByStreams:
      Rate:
        Type: Fixed
        Value: 1.23
        DefaultElement: "Unallocated Cost"
      Streams:
        - usage-stream-v1
```

## 4. Metadata Rule Type

Groups elements based on case-insensitive substring matching. Values are normalized (special characters become dashes). Useful for categorizing resources by naming patterns.

```yaml
Dimensions:
  ResourceCategory:
    Name: Resource Category
    Rules:
      - Type: Metadata
        Source: CZ:Defined:ResourceSummaryDisplay
        Values:
          - database
          - cache:
              - redis
              - memcached
          - queue:
              - sqs
              - rabbitmq
```

Values can have alternatives — `cache` matches `redis` and `memcached` as sub-patterns.

## Dimension-Level Properties

| Property | Values | Description |
|---|---|---|
| `Name` | string | Display name in Explorer (optional, defaults to DimensionId) |
| `Type` | `Allocation` or `Grouping` | Dimension type (optional, default: `Grouping`) |
| `Hide` | true/false | Hide from Explorer UI but allow as source (default: false) |
| `Disable` | true/false | Stop computing entirely (default: false) |
| `DefaultValue` | string | Element for unmatched charges. Omit unless you need a specific named bucket — defaults to "Not in Dimension" |
| `Child` | DimensionId | Next drill-down dimension in Explorer |
| `Override` | `CZ:Defined:<DimensionId>` | Replace a built-in CZ dimension with your own |
| `Source` / `Sources` | string / list | Default source(s) inherited by all rules |
| `CoalesceSources` | true/false | Use first non-null source (default: false) |
| `Transforms` | list | Default transforms inherited by all rules |

## Dimension Studio vs. CostFormation YAML

| Feature | Dimension Studio (UI) | CostFormation YAML |
|---|---|---|
| Version-controllable | No | Yes |
| Supports all features | Subset | Full |
| Fixed-weight allocation | No | Yes |
| ForEachElementOf | No | Yes |
| Agent-friendly | No | Yes |

Agents should always write YAML.

---

## Hierarchy Design Principles

When building multi-level dimension structures (e.g., Product → Team → Service), follow these five principles:

1. **Top level = business alignment.** The root dimension should map to a category that business stakeholders recognize — product, business unit, cost center. Avoid purely technical groupings at the top level.

2. **2-3 levels deep maximum.** Deeper hierarchies increase maintenance burden and make it harder for end users to navigate cost data. If you find yourself designing 4+ levels, consider whether the lower levels belong in a separate analysis dimension instead.

3. **Use Child relationships for drill-down.** Define subordinate dimensions with `Parent` pointing to the higher-level dimension ID. This preserves the ability to report at any level without duplicating classification logic.

4. **Hide intermediate dimensions.** Dimensions that exist solely to feed a parent or to stage logic for a GroupBy should be marked `Hidden: true`. Expose only the dimensions users need to interact with directly in the UI.

5. **`DefaultValue` at the top level only, and only when explicitly needed.** A catch-all bucket (e.g., "Other") makes sense on the root dimension when unclassified spend must be visible. Do not set `DefaultValue` on hidden or intermediate dimensions — it forces processing of every line item and inflates the expansion factor.
