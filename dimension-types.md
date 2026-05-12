# Dimension Types

## 1. Standard (Filter/GroupBy) Dimensions

Assigns each charge to exactly one element. Used for filtering and grouping in Explorer and Views.

```yaml
Dimensions:
  Environment:
    Name: Environment
    DefaultValue: Unknown
    Rules:
      - Name: Production
        Value: Production
        Conditions:
          - Or:
            - Match:
                Source: Account
                Values: ["111111111111", "222222222222"]
            - Match:
                Source: Tag:env
                Value: production
      - Name: Staging
        Value: Staging
        Conditions:
          - Match:
              Source: Tag:env
              Value: staging
```

## 2. Child Dimensions

Inherit structure from a parent dimension, adding transforms or overrides. Useful for deriving a coarser dimension from a finer one.

```yaml
Dimensions:
  Country:
    Name: Custom Country Dimension
    DefaultValue: global
    Child: Region
    Rules:
      - Type: GroupBy
        Source: Region
        Transforms:
          - Type: Split
            Delimiter: "-"
            Index: 0    # extracts "us" from "us-east-1"
```

## 3. Allocation Dimensions

Splits shared costs proportionally across elements. Two subtypes:

### 3a. Rules-Based Allocation

Splits based on another dimension's element spend ratios. No telemetry required.

```yaml
Dimensions:
  SharedInfraByProduct:
    Type: Allocation
    Name: Shared Infra Allocated by Product
    AllocateByRules:
      SpendToAllocate:
        - Conditions:
            - Match:
                Source: Account
                Value: "shared-infra-account-id"
      AcrossElements:
        Source: User:Defined:Product
```

### 3b. Telemetry-Based Allocation

Splits based on real usage signals sent via the Telemetry API. Most precise, but requires instrumentation. See `telemetry.md`.

```yaml
Dimensions:
  Customer:
    Type: Allocation
    Name: Cost per Customer
    Hide: False
    Disable: False
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
        - Conditions:
            - Match:
                Source: User:Defined:AllocationTargetSpend
                Value: Shared Resources
      AcrossElements:
        Rules:
          - Type: GroupBy
            Source: User:Defined:Team
```

See `allocation-design.md` for the full set of allocation design rules including the common "Spend to Allocate" dimension pattern, anti-overlap, and anti-layering.

## Dimension Studio vs. CostFormation YAML

| Feature | Dimension Studio (UI) | CostFormation YAML |
|---|---|---|
| Version-controllable | ❌ | ✅ |
| Supports all features | Subset | Full |
| Fixed-weight allocation | ❌ | ✅ |
| ForEachElementOf | ❌ | ✅ |
| Agent-friendly | ❌ | ✅ |

Agents should always write YAML.
