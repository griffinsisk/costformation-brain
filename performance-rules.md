# Performance Rules

**Read this file before generating any dimension definition.**

Everything CostFormation computes is stored and reprocessed in Snowflake. Bad patterns don't just produce wrong results — they directly increase CloudZero's infrastructure cost.

---

## ❌ Anti-Pattern 1: Matching on Raw `ResourceId`

`ResourceId` contains raw instance IDs. It is extremely high cardinality and inconsistent across cloud providers.

```yaml
# BAD
- Source: ResourceId
  Contains: "payments"
```

```yaml
# GOOD — use CloudZero's normalized resource summary
- Source: CZ:Defined:ResourceSummaryDisplay
  Contains: "payments"
```

`CZ:Defined:ResourceSummaryDisplay` groups logically related resources together, dramatically reducing cardinality and improving Explorer performance.

---

## ❌ Anti-Pattern 2: Broad `Matches` (Regex) on High-Cardinality Fields

`Matches` is evaluated row-by-row with no index benefit. Broad patterns on high-cardinality sources scan the entire dataset.

```yaml
# BAD — broad regex on a tag with many unique values
- Source: Tag:description
  Matches: ".*payments.*"
```

```yaml
# GOOD — use Contains instead
- Source: Tag:description
  Contains: "payments"
```

Use `Equals` → `BeginsWith`/`EndsWith` → `Contains` → `Matches` in that order of preference.

---

## ❌ Anti-Pattern 3: Too Many Elements in One Dimension

More elements = more rows stored per charge in Snowflake. If a dimension generates more elements than the org's cutoff threshold, excess elements collapse into `DefaultValue`.

- Rule of thumb: dimensions with >200 distinct active elements should be reviewed
- For high-cardinality use cases (e.g. cost per customer with 10,000 customers), confirm the element cutoff threshold with CloudZero support before going live

---

## ❌ Anti-Pattern 4: Redundant Telemetry Streams

If two streams cover the same resources for the same time period, the lower-priority stream is still **stored and processed** but its allocations are discarded. Redundant streams waste storage without benefit.

---

## ⚠️ Anti-Pattern 5: Unnecessary `DefaultValue`

`DefaultValue` forces the dimension to process **every line item** in billing data, even those that don't match any rule. This directly increases Snowflake compute and storage.

**When to set `DefaultValue`:**
- The dimension is a **top-level Explorer filter** where users expect a catch-all bucket (e.g., `DefaultValue: Other`)
- The dimension is used in `SpendToAllocate` and you need unmatched charges to land somewhere

**When to omit `DefaultValue` (preferred for performance):**
- Hidden/helper dimensions (`Hide: true`) used only as references by other dimensions
- Dimensions where you only care about matched charges

**Use `HasValue: false` instead** when other dimensions need to reference "charges not covered by this dimension":

```yaml
# GOOD — no DefaultValue, uses HasValue: false to find uncovered charges
SharedFilter:
  Name: Shared Infrastructure Filter
  Hide: true
  Rules:
    - Type: Group
      Name: Shared Resources
      Conditions:
        - Source: Tag:shared
          Equals: "true"

NonSharedResources:
  Name: Non-Shared Resources
  Rules:
    - Type: Group
      Name: Non-Shared
      Conditions:
        - Source: User:Defined:SharedFilter
          HasValue: false

# BAD — DefaultValue forces processing every line item
SharedFilter:
  Name: Shared Infrastructure Filter
  Hide: true
  DefaultValue: Not Shared     # Processes every line item!
  Rules:
    - Type: Group
      Name: Shared Resources
      Conditions:
        - Source: Tag:shared
          Equals: "true"
```

---

## ✅ Pattern 6: Use `ForEachElementOf` to Reduce Expansion Factor

`ForEachElementOf` partitions allocations by a parent dimension (e.g., Region or Account), which **reduces** the expansion factor when the alternative is a single global allocation across many elements.

**Expansion Factor Formula:** `targeted line items × allocation elements`

Without `ForEachElementOf`: a shared resource used by 100 teams creates 100 line items per charge, even if each region only contains a few teams.

With `ForEachElementOf: Region`: allocation runs per-region, so each charge only expands to the teams in that specific region (e.g., 3 instead of 100).

```yaml
# GOOD — partitioned allocation reduces expansion
SharedResourceAllocation:
  Type: Allocation
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

**When NOT to use it**: if the partitioning dimension has very high cardinality itself (e.g., 500+ elements), the per-partition overhead may outweigh the benefit. Best for low-to-medium cardinality partitions like Region, Account, or Environment.

---

## ❌ Anti-Pattern 7: Overlapping Allocation Dimensions

When multiple allocation dimensions have overlapping `SpendToAllocate` conditions, the same line items are allocated multiple times, causing significant row expansion and performance degradation.

**Fix: Create a common "Spend to Allocate" dimension** that acts as the single source of truth for all allocation dimensions:

```yaml
# GOOD — single hidden dimension partitions spend, no overlap
AllocationTargetSpend:
  Name: Allocation Target Spend
  Hide: true
  Rules:
    - Type: Group
      Name: Shared Database
      Conditions:
        - Source: Service
          Equals: AmazonRDS
        - Source: Tag:allocation-target
          Equals: shared-db
    - Type: Group
      Name: Shared Compute
      Conditions:
        - Source: Service
          Equals: AmazonEC2
        - Source: Tag:allocation-target
          Equals: shared-compute

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

# BAD — overlapping conditions
DatabaseAllocation:
  Type: Allocation
  AllocateByRules:
    SpendToAllocate:
      Conditions:
        - Source: Tag:shared
          Equals: "true"      # Could overlap with ComputeAllocation!

ComputeAllocation:
  Type: Allocation
  AllocateByRules:
    SpendToAllocate:
      Conditions:
        - Source: Tag:shared
          Equals: "true"      # Same condition = overlap!
```

---

## ❌ Anti-Pattern 8: Layered Allocation Dimensions

When an allocation dimension references another allocation dimension's output in its `SpendToAllocate`, it causes **exponential row expansion** — each layer multiplies the rows from the previous layer.

```yaml
# BAD — layered allocations
FirstLevelAllocation:
  Type: Allocation
  AllocateByRules:
    # ... allocation logic

SecondLevelAllocation:
  Type: Allocation
  AllocateByRules:
    SpendToAllocate:
      Conditions:
        - Source: User:Defined:FirstLevelAllocation  # Layering!
          Equals: SomeValue
```

**Fix**: keep allocation dimensions independent. If you need to combine allocated costs, use a standard (non-allocation) dimension that references allocation outputs via `GroupBy` (see Example 9 in `examples.md`).

---

## ❌ Anti-Pattern 9: Broad `SpendToAllocate` Scope

In Allocation Dimensions, the larger the spend pool being split, the more Snowflake rows the allocation engine writes. Always scope `SpendToAllocate` as tightly as possible.

```yaml
# BAD — allocates all charges in the org
SpendToAllocate:
  - Conditions: []

# GOOD — allocates only the specific shared account + service
SpendToAllocate:
  Conditions:
    - And:
      - Source: Account
        Equals: "shared-infra-account-id"
      - Source: Service
        Equals: AmazonRDS
```

---

## ✅ Summary Checklist

Before finalizing any dimension:

- [ ] Am I using `CZ:Defined:ResourceSummaryDisplay` instead of `ResourceId`?
- [ ] Have I avoided `Matches` (regex) where Equals/Contains would work?
- [ ] Is element count expected to stay under 200?
- [ ] Is `DefaultValue` only set on dimensions that need it (top-level Explorer filters)? Have I used `HasValue: false` for hidden/helper dimensions?
- [ ] Is `SpendToAllocate` scoped as narrowly as possible?
- [ ] Do multiple allocation dimensions share a common "Spend to Allocate" dimension to prevent overlap?
- [ ] Am I avoiding layered allocations (allocation referencing allocation)?
- [ ] Have I considered `ForEachElementOf` to reduce expansion factor for proportional allocations?
- [ ] Are telemetry streams non-redundant?
- [ ] Am I using reusable hidden base dimensions instead of copy-pasting logic?
