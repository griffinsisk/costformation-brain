# Core Concepts

| Term | Meaning |
|---|---|
| **Dimension** | A lens on cost — like "Environment" or "Customer" |
| **Element** | A value within a dimension — like "Production" or "Acme Corp" |
| **Charge** | A single billing line item from a cloud provider |
| **Rule** | A named condition block that assigns charges to an element |
| **Source** | The billing field or tag being evaluated |
| **Condition** | A filter expression (Equals, Contains, StartsWith, And, Or, Not…) |
| **Transform** | A mutation applied to a source value before matching |
| **Allocation Dimension** | A special dimension that splits charges across elements proportionally |
| **Telemetry Stream** | Usage data sent via API used to weight allocation proportions |
| **DefaultValue** | The element assigned when no rule matches — always set this |
| **Hide** | Whether the dimension appears in Explorer UI |
| **Disable** | Whether the dimension is still computed but hidden everywhere |

## How It Fits Together

Every cloud billing charge flows through each published dimension. For each charge, CostFormation evaluates rules top-to-bottom until one matches and assigns the charge to that rule's element. If no rule matches, the charge goes to `DefaultValue` (if set) or the charge is simply not covered by that dimension.

Everything an agent generates ends up stored and reprocessed in **Snowflake** — inefficient definitions multiply cost at query time.

## Design Principles

1. **Use good abstractions** — map dimensions to core business concepts (teams, products, environments), not implementation details. Create reusable hidden base dimensions and reference them via `User:Defined:` instead of duplicating logic.

2. **Performance-first** — dimension cost is driven by the number of line items processed and (for allocations) the expansion factor. Avoid `DefaultValue` on helper dimensions. Scope `SpendToAllocate` narrowly. See `performance-rules.md`.

3. **Modular, composable dimensions** — build smaller focused dimensions that combine, rather than monolithic dimensions trying to do everything. A hidden filter dimension referenced by three allocation dimensions is better than three allocation dimensions each duplicating the same filter logic.
