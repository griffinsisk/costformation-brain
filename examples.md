# Worked Examples

Ten real-world-derived examples, each demonstrating a distinct CostFormation pattern. Examples progress from simple to complex.

---

## Example 1: Account Name Mapping (Hidden + Child)

Pattern: map AWS account IDs to human-readable names, hidden from Explorer, with Service as a child dimension for drill-down.

```yaml
Dimensions:
  AccountName:
    Name: Account Name
    Hide: true
    Child: Service
    Source: Account
    Rules:
      - Type: Group
        Name: Production (389949659813)
        Conditions:
          - Equals: "389949659813"
      - Type: Group
        Name: Staging (323150190480)
        Conditions:
          - Equals: "323150190480"
      - Type: Group
        Name: Sandbox (024848463391)
        Conditions:
          - Equals: "024848463391"
```

**Why this works:**
- `Hide: true` keeps it out of Explorer — used only as a reference dimension by other definitions
- `Child: Service` lets Explorer drill from account name → service when needed
- `Source: Account` at dimension level means rules inherit it — no need to repeat per-rule
- Short, flat list of `Equals` conditions is the cheapest possible Snowflake operation

---

## Example 2: Department via Account Lists

Pattern: group many AWS accounts into business departments. Good for orgs with 20+ accounts that map cleanly to org chart.

```yaml
Dimensions:
  Department:
    Name: Department
    DefaultValue: Unassigned    # intentional — top-level Explorer filter needs a named catch-all
    Rules:
      - Type: Group
        Name: Customer Operations
        Conditions:
          - Source: Account
            Equals:
              - "233466153464"
              - "767397799312"
              - "497723851829"
              - "572656853062"
      - Type: Group
        Name: Engineering
        Conditions:
          - Source: Account
            Equals:
              - "284954390955"
              - "414666106671"
              - "585876524959"
              - "654654353366"
              - "605134457544"
      - Type: Group
        Name: IT
        Conditions:
          - Source: Account
            Equals:
              - "400210543042"
              - "034491712127"
      - Type: Group
        Name: Sales
        Conditions:
          - Source: Account
            Equals: "073933415963"
```

**Why this works:**
- Multi-value `Equals` lists are efficient — Snowflake evaluates them as an IN clause
- Each account maps to exactly one department, so rule order doesn't matter
- `DefaultValue: Unassigned` catches new accounts added after the definition is published

---

## Example 3: Environment with Multi-Source Matching (Tags + Accounts + Resources + K8s)

Pattern: classify charges by environment using every available signal — tags, account names, resource names, and K8s labels. A good dimension catches charges from ALL sources.

```yaml
Dimensions:
  Environment:
    Name: Environment
    Rules:
      - Type: Group
        Name: production
        Conditions:
          - Source: Account
            Equals: "389949659813"
          - Sources:
              - K8s:Label:chain_link_env
              - K8s:Label:chain.link/env
              - Tag:chain.link/env
              - Tag:environment
              - Tag:Env
              - Tag:env
            Contains:
              - prod
              - Prod
          - Source: CZ:Defined:ResourceSummaryDisplay
            Contains: "-prod"
      - Type: Group
        Name: staging
        Conditions:
          - Sources:
              - K8s:Label:chain_link_env
              - K8s:Label:chain.link/env
              - Tag:chain.link/env
              - Tag:environment
              - Tag:Env
              - Tag:env
            Contains:
              - stag
          - Source: CZ:Defined:ResourceSummaryDisplay
            Contains: "-staging"
      - Type: Group
        Name: sandbox
        Conditions:
          - Source: Account
            Equals:
              - "024848463391"
              - "389435844244"
          - Sources:
              - K8s:Label:chain_link_env
              - K8s:Label:chain.link/env
              - Tag:chain.link/env
              - Tag:environment
              - Tag:Env
              - Tag:env
            Contains:
              - sandbox
      - Type: GroupBy
        Sources:
          - K8s:Label:chain_link_env
          - K8s:Label:chain.link/env
          - Tag:chain.link/env
          - Tag:environment
          - Tag:Env
          - Tag:env
        CoalesceSources: true
```

**Why this works:**
- **Multiple signal types per rule** — tags, account IDs, AND resource names all feed into the same environment element. Charges are caught regardless of which signal is present.
- `CZ:Defined:ResourceSummaryDisplay` catches resources named `rg-insightapi-prod`, `czbg-cluster-prod`, etc. that may not have environment tags but carry environment signals in their names
- `Sources` (plural) checks multiple K8s labels and tags in one condition — no need for nested `Or`
- `CoalesceSources: true` on the GroupBy catch-all picks the first non-null value across all listed sources
- No `DefaultValue` — CostFormation defaults to "Not in Dimension" which is sufficient

---

## Example 4: Product with Complex And/Or/Not Logic

Pattern: map charges to products using nested boolean logic across K8s labels, tags, and resource names. Demonstrates how to exclude false positives.

```yaml
Dimensions:
  Product:
    Name: Product
    DefaultValue: Unassigned    # intentional — top-level Explorer filter needs a named catch-all
    Sources:
      - K8s:Label:chain.link/product
      - Tag:chain.link/product
    Rules:
      - Type: Group
        Name: Automation
        Conditions:
          - Equals: automation
          - And:
              - Source: Service
                Equals: AmazonCloudWatch
              - Source: CZ:Defined:ResourceSummaryDisplay
                Contains:
                  - automation
                  - keepers
          - And:
              - Sources:
                  - K8s:Label:chain.link/product
                  - K8s:Label:chain.link/component
                  - K8s:Namespace
                  - Tag:chain.link/product
                  - CZ:Defined:ResourceSummaryDisplay
                Contains:
                  - automation
                  - keeper
              - Not:
                  - Sources:
                      - K8s:Namespace
                      - K8s:Workload
                      - CZ:Defined:ResourceSummaryDisplay
                    Contains:
                      - gatekeeper
                      - zookeeper
      - Type: Group
        Name: CCIP
        Conditions:
          - Equals: ccip
          - And:
              - Source: User:Defined:AccountName
                BeginsWith: AWS - Security
              - Source: Tag:rmn
                Equals: "true"
```

**Why this works:**
- Dimension-level `Sources` means the simple `Equals: automation` check runs against all listed sources automatically
- `Not` block prevents false positives — "gatekeeper" and "zookeeper" contain "keeper" but aren't part of the Automation product
- Multiple top-level conditions under a rule are OR'd — any match assigns the charge
- `And` blocks combine conditions that must all be true together
- `CZ:Defined:ResourceSummaryDisplay` instead of `ResourceId` keeps Snowflake costs down

---

## Example 5: Team with Child Dimension and GroupBy Fallback

Pattern: explicit team rules for known teams, with a GroupBy catch-all that auto-discovers new teams from tags. Child dimension enables drill-down by environment.

```yaml
Dimensions:
  Team:
    Name: Team
    DefaultValue: Unassigned    # intentional — top-level Explorer filter needs a named catch-all
    Child: User:Defined:Environment
    Rules:
      - Type: Group
        Name: real-time-streaming-platform
        Conditions:
          - Source: Tag:team
            Equals: rtsp
          - Source: Tag:chain.link/team
            Equals:
              - rtsp
              - real-time
              - real-time-streaming-platform
      - Type: Group
        Name: data-streams
        Conditions:
          - Source: User:Defined:Product
            Contains: data-streams
      - Type: GroupBy
        Sources:
          - K8s:Label:chain.link/team
          - Tag:chain.link/team
          - Tag:team
        CoalesceSources: true
```

**Why this works:**
- `Child: User:Defined:Environment` enables Team → Environment drill-down in Explorer
- Explicit Group rules come first for teams needing special matching logic (e.g. `rtsp` alias)
- The second rule cross-references `User:Defined:Product` — charges already classified as "data-streams" product map to the data-streams team
- `GroupBy` at the end auto-discovers any team value from tags/labels without needing explicit rules
- `CoalesceSources` picks the first non-null tag across multiple naming conventions

---

## Example 6: GroupBy with Transforms (Split + Lower)

Pattern: extract structured values from resource names or normalize casing with transforms.

### 6a: Extract Node Pool from Azure Resource Names

```yaml
Dimensions:
  AKS_NodePool:
    Name: AKS Node Pool
    Rules:
      - Type: GroupBy
        Sources:
          - Resource                    # raw CZRN — prefer CZ:Defined:ResourceSummaryDisplay for most use cases
        Transforms:
          - Type: Split
            Delimiter: "|"
            Index: 1
        Conditions:
          - Contains: vmss
```

### 6b: Normalize K8s Labels to Lowercase

```yaml
Dimensions:
  NetworkType:
    Name: Network Type
    Rules:
      - Type: GroupBy
        Sources:
          - Tag:chain.link/network-type
          - K8s:Label:chain.link/network-type
          - K8s:Label:app.chain.link/network_type
        CoalesceSources: true
        Transforms:
          - Type: Lower
```

**Why this works:**
- **Split** parses structured strings — Azure resource names often encode metadata in pipe-delimited segments
- The `Conditions` filter ensures the transform only runs on relevant resources (those containing "vmss")
- **Lower** normalizes inconsistent casing from K8s labels and tags so `Mainnet` and `mainnet` collapse to one element
- Transforms run before the GroupBy evaluates — the pipeline is: source → transform → condition → element assignment

---

## Example 7: Telemetry-Based Allocation (AllocateByStreams)

Pattern: split shared costs proportionally using usage signals sent via the Telemetry API.

```yaml
Dimensions:
  SplitObservabilityLogs:
    Name: Split Observability Logs by Product
    Type: Allocation
    AllocateByStreams:
      Streams:
        - observability-logs-bytes-received-v2

  SplitObservabilityMetrics:
    Name: Split Observability Metrics by Product
    Type: Allocation
    AllocateByStreams:
      Streams:
        - observability-metrics-series-received-v2

  SplitSharedGCP:
    Name: Split Shared GCP by Product
    Type: Allocation
    AllocateByStreams:
      Streams:
        - gcp-telemetry-v1
```

Companion telemetry sender (Python):
```python
import requests

records = [
    {
        "filter": {"element_tag": product_name},
        "value": bytes_received,
        "timestamp": hour_utc.strftime("%Y-%m-%dT%H:00:00Z"),
        "granularity": "HOURLY"
    }
    for product_name, bytes_received in hourly_log_bytes.items()
]

requests.post(
    "https://api.cloudzero.com/v1/telemetry/observability-logs-bytes-received-v2",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"records": records}
)
```

**Why this works:**
- Each stream measures a distinct usage signal — log bytes, metric series, or GCP resource consumption
- Stream names include a version suffix (`-v2`) making it safe to evolve the signal without breaking existing allocations
- One dimension per stream keeps allocations focused and debuggable
- Telemetry records must use UTC, hourly-aligned timestamps (see `telemetry.md`)

---

## Example 8: Rules-Based Proportional Allocation with HasValue Guards

Pattern: allocate shared costs proportionally across products using rule-based matching. Uses `HasValue` to avoid double-counting already-allocated spend.

```yaml
Dimensions:
  SplitSharedCostToProduct:
    Name: Split Shared Costs to Product
    Type: Allocation
    AllocateByRules:
      AllocationMethod: Proportional
      SpendToAllocate:
        Conditions:
          - Source: User:Defined:SplitSharedProductsWithTelemetry
            Equals:
              - "Shared -> RPC - Proxy - Chainlink Misc"
              - "Shared -> RPC - Proxy - Chainlink Util"
          - And:
              - Source: User:Defined:SharedProducts
                Equals:
                  - "Shared -> Platform - Enterprise Support"
                  - "Shared -> Platform - Network"
                  - "Shared -> Platform - Tools"
              - Source: User:Defined:Product
                HasValue: false
      AcrossElements:
        Rules:
          - Type: GroupBy
            Source: User:Defined:Product
            Conditions:
              - Source: User:Defined:Product
                HasValue: true
```

**Why this works:**
- `SpendToAllocate` is narrowly scoped to specific shared cost categories — not "all untagged spend"
- `HasValue: false` guard ensures only truly unallocated charges enter the allocation pool — charges already assigned to a Product are excluded
- `AcrossElements` with `GroupBy Source: User:Defined:Product` distributes proportionally based on each product's existing direct spend
- Multiple conditions under `SpendToAllocate` are OR'd — any matching shared category is included in the pool

---

## Example 9: Chained Dimension Pipeline (Shared Allocations → Product Allocated)

Pattern: compose multiple allocation dimensions into a single "fully allocated" view by referencing their outputs as sources.

```yaml
Dimensions:
  # Step 1: Individual allocation dimensions (each defined elsewhere)
  # - SplitSharedGCP (telemetry-based)
  # - SplitObservabilityLogs (telemetry-based)
  # - SplitSharedCostToProduct (rules-based)

  # Step 2: Aggregate all allocation outputs into one reference dimension
  SharedAllocations:
    Name: Shared Allocations
    Sources:
      - User:Defined:SplitSharedGCP
      - User:Defined:SplitObservabilityLogs
      - User:Defined:SplitSharedCostToProduct
      - User:Defined:SplitSharedAtlasCost
    Rules:
      - Type: Group
        Name: CCIP
        Conditions:
          - Equals: CCIP
      - Type: Group
        Name: Data Feeds
        Conditions:
          - Equals: Data Feeds
      - Type: Group
        Name: Automation
        Conditions:
          - Equals: Automation

  # Step 3: Final "Product Allocated" combines direct + allocated costs
  ProductAllocated:
    Name: Product Allocated
    Sources:
      - User:Defined:SharedAllocations
      - User:Defined:Product
    Rules:
      - Type: Group
        Name: CCIP
        Conditions:
          - Equals: CCIP
      - Type: Group
        Name: Data Feeds
        Conditions:
          - Equals: Data Feeds
      - Type: Group
        Name: Automation
        Conditions:
          - Equals: Automation
```

**Why this works:**
- Each allocation dimension handles one concern (GCP, observability, shared infra) independently
- `SharedAllocations` aggregates outputs from multiple allocation dimensions using `Sources` (plural)
- `ProductAllocated` merges direct product costs (`User:Defined:Product`) with allocated shared costs (`User:Defined:SharedAllocations`)
- Element names must match across the chain — "CCIP" in the allocation output must match "CCIP" in the aggregator rules
- This pattern scales: adding a new allocation dimension means adding one more `Source` entry, not rewriting the pipeline

---

## Example 10: Capturing Unallocated AWS Infrastructure (HasValue + __UNALLOCATED__)

Pattern: identify unallocated K8s and Savings Plan costs that don't belong to any product. Uses multi-dimensional `HasValue: false` checks and the special `__UNALLOCATED__` K8s marker.

```yaml
Dimensions:
  SharedAWS:
    Name: Shared AWS
    Rules:
      - Type: Group
        Name: Platform Underutilization Costs
        Conditions:
          - And:
              - Source: CloudProvider
                Equals: AWS
              - Source: Service
                Equals: ComputeSavingsPlans
              - Source: CZ:Defined:Category
                Equals: "Non-Usage: SavingsPlanRecurringFee"
              - Source: User:Defined:Product
                HasValue: false
      - Type: Group
        Name: Unallocated K8s Infrastructure
        Conditions:
          - And:
              - Source: CloudProvider
                Equals: AWS
              - Source: K8s:Namespace
                Equals: __UNALLOCATED__
              - Source: K8s:Workload
                Equals: __UNALLOCATED__
              - Sources:
                  - User:Defined:Product
                  - User:Defined:SharedAtlas
                  - User:Defined:SharedObservability
                HasValue: false
      - Type: Group
        Name: Other Shared Resources
        Conditions:
          - And:
              - Source: CloudProvider
                Equals: AWS
              - Source: User:Defined:CostCenter
                Equals: platform
              - Source: User:Defined:Team
                Equals: infra-platform
              - Not:
                  - Source: User:Defined:Component
                    Equals: eks
```

**Why this works:**
- `__UNALLOCATED__` is CloudZero's K8s marker for compute that isn't attributed to any workload — it's real cost that needs a home
- Multi-source `HasValue: false` checks against Product, SharedAtlas, and SharedObservability ensure only truly orphaned charges are captured
- `CZ:Defined:Category` identifies Savings Plan non-usage fees — a common source of "invisible" shared cost
- `Not` block excludes EKS charges that are handled by a different dimension
- This dimension acts as the "safety net" — what it captures should shrink over time as more direct attribution is added
