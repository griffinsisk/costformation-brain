# CostFormation Best Practices (Internal Engineering Reference)

Source: CloudZero Confluence — Matt Yellen, updated Aug 11, 2025

## Overview

Effective CostFormation implementation requires balancing business requirements with system performance.

## Core Design Principles

### 1. Use Good Abstractions

- **Map dimensions to core business concepts** — reflect teams, products, environments, not technical implementation details
- **Avoid copy/pasting logic** — create reusable base dimensions and reference them
- **Create modular, composable dimensions** — smaller focused dimensions that combine, not monoliths

**Good: Create a hidden base dimension for shared logic, reference it elsewhere:**
```yaml
SharedInfrastructureFilter:
  Name: Shared Infrastructure Filter
  Hide: true
  Rules:
    - Type: Group
      Name: Shared Resources
      Conditions:
        - And:
          - Source: Tag:shared
            Equals: "true"
          - Source: Tag:environment
            Equals: [prod, production]

# Reference the base dimension in allocation logic
ProductAllocation:
  Type: Allocation
  AllocateByRules:
    SpendToAllocate:
      Conditions:
        - Source: User:Defined:SharedInfrastructureFilter
          Equals: Shared Resources

NonSharedResources:
  Name: Non-Shared Resources
  Rules:
    - Type: Group
      Name: Non-Shared Resources
      Conditions:
        - Source: User:Defined:SharedInfrastructureFilter
          HasValue: false
```

**Bad: Duplicating the same complex logic in multiple places.**

### 2. Performance-First Design

Dimension performance is directly impacted by the number of line items they process and (for allocation dimensions) what they produce.

## Default Value Best Practices

### Avoid DefaultValue Unless Necessary

**Key Principle:** Using `DefaultValue` forces the dimension to process EVERY line item in billing data. This is a performance killer.

**Use `HasValue: false` instead:**

```yaml
# Good: Only processes line items with the specific tag
Environment:
  Name: Environment
  Rules:
    - Type: Group
      Name: Production
      Conditions:
        - Source: Tag:environment
          Equals: [prod, production]
    - Type: Group
      Name: Development
      Conditions:
        - Source: Tag:environment
          Equals: [dev, development]

# Reference with HasValue for untagged resources
CostByEnvironment:
  Name: Cost by Environment
  Rules:
    - Type: Group
      Name: Tagged Resources
      Conditions:
        - Source: User:Defined:Environment
          HasValue: true
    - Type: Group
      Name: Untagged Resources
      Conditions:
        - Source: User:Defined:Environment
          HasValue: false
```

```yaml
# Bad: Forces processing of ALL line items
Environment:
  Name: Environment
  DefaultValue: Untagged  # This processes every line item!
```

## Telemetry Allocation Best Practices

### Create Dedicated Telemetry Target Dimensions

**Key Principle:** Telemetry is difficult to change once sent, but dimensions are easy to modify. Use dedicated "telemetry target" dimensions as stream filters to future-proof allocations.

```yaml
# Good: Dedicated hidden telemetry target dimension
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

Telemetry records reference the target dimension in their filters:
```json
{
  "timestamp": "2020-01-25T00:00:00Z",
  "granularity": "DAILY",
  "filter": {
    "custom:ApplicationTelemetryTarget": ["WebApp"],
    "tag:environment": ["prod"]
  },
  "element-name": "team-alpha",
  "value": "250000000"
}
```

Then the allocation dimension references the stream:
```yaml
ApplicationResourceAllocation:
  Type: Allocation
  AllocateByStreams:
    Streams:
      - application_resource_usage
```

**Bad:** Referencing tags directly in telemetry streams (harder to maintain when tag values change).

## Allocation Dimension Performance

### Consider Expansion Factors

**Expansion Factor Formula:** `Number of targeted line items × Number of allocation elements`

### Keep Allocations Narrowly Scoped

Target only specific costs that need allocation, not broad categories.

```yaml
# Good: Narrowly scoped
SharedDatabaseAllocation:
  Type: Allocation
  AllocateByRules:
    AllocationMethod: Proportional
    SpendToAllocate:
      Conditions:
        - Source: Service
          Equals: Amazon RDS
        - Source: Tag:shared
          Equals: "true"
        - Source: Tag:resource-type
          Equals: database
```

```yaml
# Bad: Overly broad — could target thousands of line items
AllInfrastructureAllocation:
  Type: Allocation
  AllocateByRules:
    AllocationMethod: Proportional
    SpendToAllocate:
      Conditions:
        - Source: Tag:shared
          Equals: "true"
```

**Note:** CZ doesn't currently have tools for evaluating line item count while building. The Organization Data Projection Size dashboard is available after publishing, primarily for diagnosing problems, not preventing them.

### Avoid Overlapping Allocation Dimensions

**Key Principle:** Overlapping allocations cause significant row expansion and performance degradation.

**Solution: Create a single common "Spend to Allocate" dimension:**

```yaml
# Good: Single common dimension guarantees no overlap
AllocationTargetSpend:
  Name: Allocation Target Spend
  Hide: true
  Rules:
    - Type: Group
      Name: Shared Database
      Conditions:
        - Source: Service
          Equals: Amazon RDS
        - Source: Tag:allocation-target
          Equals: shared-db
    - Type: Group
      Name: Shared Compute
      Conditions:
        - Source: Service
          Equals: Amazon EC2
        - Source: Tag:allocation-target
          Equals: shared-compute

# Each allocation references a specific element — no overlap possible
DatabaseAllocation:
  Type: Allocation
  AllocateByRules:
    AllocationMethod: Proportional
    SpendToAllocate:
      Conditions:
        - Source: User:Defined:AllocationTargetSpend
          Equals: Shared Database

ComputeAllocation:
  Type: Allocation
  AllocateByRules:
    AllocationMethod: Proportional
    SpendToAllocate:
      Conditions:
        - Source: User:Defined:AllocationTargetSpend
          Equals: Shared Compute
```

```yaml
# Bad: Same condition in multiple allocations = overlap
DatabaseAllocation:
  Type: Allocation
  AllocateByRules:
    SpendToAllocate:
      Conditions:
        - Source: Tag:shared
          Equals: "true"  # Overlaps!

ComputeAllocation:
  Type: Allocation
  AllocateByRules:
    SpendToAllocate:
      Conditions:
        - Source: Tag:shared
          Equals: "true"  # Same condition = overlap!
```

### Avoid "Layering" Allocation Dimensions

**Key Principle:** When allocation dimensions reference other allocation dimensions (directly or indirectly), it causes exponential row expansion.

```yaml
# Bad: Layered allocations
FirstLevelAllocation:
  Type: Allocation
  # ...

SecondLevelAllocation:
  Type: Allocation
  AllocateByRules:
    SpendToAllocate:
      Conditions:
        - Source: User:Defined:FirstLevelAllocation  # Layering!
          Equals: SomeValue
```

### Use ForEachElementOf for Proportional Allocations

**Key Principle:** `ForEachElementOf` partitions allocations (e.g., by Region or Account), significantly reducing the expansion factor.

```yaml
SharedResourceAllocation:
  Type: Allocation
  AllocateByRules:
    AllocationMethod: Proportional
    ForEachElementOf: Region  # Partitions by region
    SpendToAllocate:
      Conditions:
        - Source: User:Defined:AllocationTargetSpend
          Equals: Shared Resources
    AcrossElements:
      Rules:
        - Type: GroupBy
          Source: User:Defined:Team
```

- **Without ForEachElementOf:** 100 teams = 100 line items per shared resource
- **With ForEachElementOf: Region:** only creates line items for teams in each region (e.g., 3 teams per region = expansion factor of 3, not 100)

## Summary of Rules

1. **Use good abstractions** — hidden base dimensions, reference them, don't copy/paste
2. **Avoid DefaultValue** — use `HasValue: false` instead to avoid processing all line items
3. **Create dedicated telemetry target dimensions** — dimensions are easy to change, telemetry is not
4. **Keep allocations narrowly scoped** — target specific costs, not broad categories
5. **Use a single common "Spend to Allocate" dimension** — prevents overlapping allocations
6. **Never layer allocation dimensions** — causes exponential row expansion
7. **Use ForEachElementOf** — partitions allocations to reduce expansion factor
8. **Expansion Factor = targeted line items × allocation elements** — keep this small
