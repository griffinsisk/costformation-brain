# Allocation Dimension Design

**Read this file before writing any Allocation Dimension.**

Source: CloudZero Engineering CostFormation Best Practices (principal engineer who maintains Snowflake).

---

## The Expansion Factor

Allocation dimensions **split** charges, expanding the total number of line items Snowflake must store and process.

**Formula:** `targeted line items × allocation elements = total rows`

A shared database with 1,000 line items allocated across 50 teams produces 50,000 rows. Design decisions that seem small (scoping, partitioning, overlap) have multiplicative impact.

---

## Rule 1: Use a Common "Spend to Allocate" Dimension

When multiple allocation dimensions exist, create a **single hidden dimension** that categorizes all allocatable spend. Each allocation dimension then targets a specific element of that dimension.

This **guarantees no overlap** — each line item maps to exactly one allocation target.

```yaml
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
```

---

## Rule 2: Never Layer Allocations

An allocation dimension must **never** reference another allocation dimension's output in its `SpendToAllocate`. This causes exponential row expansion — each layer multiplies the rows from the previous layer.

```yaml
# BAD — exponential expansion
FirstLevelAllocation:
  Type: Allocation
  AllocateByRules:
    # ...

SecondLevelAllocation:
  Type: Allocation
  AllocateByRules:
    SpendToAllocate:
      Conditions:
        - Source: User:Defined:FirstLevelAllocation   # Layering!
          Equals: SomeValue
```

If you need to combine allocated costs into a unified view, use a **standard (non-allocation) dimension** that references allocation outputs via `GroupBy` or `Sources` — see Example 9 in `examples.md`.

---

## Rule 3: Scope `SpendToAllocate` as Tightly as Possible

Every line item in the `SpendToAllocate` pool gets expanded by the number of allocation elements. Broad scopes multiply Snowflake cost.

```yaml
# BAD — allocates everything tagged "shared" (could be thousands of line items)
SpendToAllocate:
  Conditions:
    - Source: Tag:shared
      Equals: "true"

# GOOD — narrowly scoped to specific service + resource type
SpendToAllocate:
  Conditions:
    - Source: Service
      Equals: AmazonRDS
    - Source: Tag:shared
      Equals: "true"
    - Source: Tag:resource-type
      Equals: database
```

---

## Rule 4: Use `ForEachElementOf` to Reduce Expansion

`ForEachElementOf` partitions allocations by a parent dimension, reducing the per-charge expansion factor.

**Without partitioning**: 1 shared resource × 100 teams = 100 rows per charge.

**With `ForEachElementOf: Region`**: if each region has ~3 teams, expansion is 3 rows per charge instead of 100.

```yaml
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

Best for low-to-medium cardinality partitions (Region, Account, Environment). Avoid for high-cardinality partitions (500+ elements) where the overhead of running separate passes outweighs the savings.

---

## Rule 5: Create Dedicated Telemetry Target Dimensions

Telemetry is hard to change once sent. Dimensions are easy to modify.

Instead of filtering telemetry streams by raw tags, create a hidden "target" dimension and reference it in telemetry records. If tag values change, you update the dimension — not every telemetry sender. See `telemetry.md` for the full pattern.

---

## Rule 6: Avoid `DefaultValue` on Allocation Input Dimensions

Hidden dimensions used as inputs to allocation logic (filters, targets, intermediate classifications) should **not** have `DefaultValue` set. It forces the dimension to process every line item — most of which will never participate in the allocation.

Use `HasValue: false` in downstream dimensions to identify uncovered charges instead.

---

## Monitoring

CloudZero's **Organization Data Projection Size** dashboard in Sigma shows the line item expansion caused by each dimension. Use it to diagnose performance problems after publishing. It is currently the only tool available for this — there is no pre-publish sizing estimator.
