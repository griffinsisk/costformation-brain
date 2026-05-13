# Conditions & Transforms Reference

> Transforms run first, then conditions evaluate against the transformed values. This file is ordered by execution sequence: transforms → conditions.

## Transforms (applied first)

Transforms mutate source values **before** conditions evaluate them. They are applied at the rule level and execute in listed order.

```yaml
Rules:
  - Type: Group
    Name: Production
    Conditions:
      - Source: Tag:environment
        Equals: prod
    Transforms:
      - Type: Lower   # source value lowercased before matching
```

### Available Transforms

| Transform | Effect | Example |
|---|---|---|
| `Lower` | Converts to lowercase | `ProductionResource 1` → `productionresource 1` |
| `Upper` | Converts to uppercase | `the cost types` → `THE COST TYPES` |
| `Title` | Capitalizes first letter of each word | `the cost types` → `The Cost Types` |
| `Trim` | Removes leading/trailing whitespace | `" the cost types "` → `"the cost types"` |
| `Clean` | Removes whitespace, converts `.,/#!$%^&*;:=_~()\'` and spaces to dashes | `" The:Cost!Types "` → `"The-Cost-Types"` |
| `Normalize` | Combines Lower + Trim + special-char conversion | `Production/Resources#4561` → `production-resources-4561` |
| `Split` | Splits on delimiter, extracts Nth part (**1-based index**) | See below |

### Examples

#### Lower — normalize inconsistent tag values
```yaml
Transforms:
  - Type: Lower
```

#### Normalize — clean and lowercase in one step
```yaml
Transforms:
  - Type: Normalize
```

#### Split — extract a segment from a delimited string

**Index is 1-based** — `Index: 1` extracts the first segment.

```yaml
# Extract "payments" from "payments/backend"
Transforms:
  - Type: Split
    Delimiter: "/"
    Index: 1
```

```yaml
# Extract "west" from "us-west-1"
Transforms:
  - Type: Split
    Delimiter: "-"
    Index: 2
```

#### Chaining transforms — execute in order
```yaml
Transforms:
  - Type: Lower
  - Type: Trim
```

### When to Use Transforms

- **Always use `Lower`** when matching user-applied tags — tagging is rarely consistent across teams
- Use `Normalize` when tag values have mixed casing AND special characters
- Use `Split` to extract parts from composite values rather than writing multiple `Equals` conditions
- Prefer transforms over writing duplicate rules for casing variants

---

## Conditions (evaluated against transformed values)

## Basic Conditions

All conditions are flat — `Source` and the operator are siblings, not nested under a wrapper keyword.

```yaml
# Exact match (case-sensitive by default)
- Source: Account
  Equals: "123456789012"

# Match multiple values (OR semantics within the same condition)
- Source: Service
  Equals:
    - AmazonEC2
    - AmazonRDS

# Multiple sources (checks each, first non-null wins)
- Sources:
    - Tag:environment
    - Tag:env
    - K8s:Label:environment
  Equals: production

# Begins with prefix
- Source: UsageType
  BeginsWith: "USE2-"

# Ends with suffix
- Source: Tag:env
  EndsWith: "-prod"

# Contains substring
- Source: CZ:Defined:ResourceSummaryDisplay
  Contains: "payments"

# Contains multiple (OR — matches if any substring is found)
- Source: CZ:Defined:ResourceSummaryDisplay
  Contains:
    - payments
    - billing

# Regex match (Matches) — uses Snowflake REGEXP_LIKE syntax. Use sparingly, see performance-rules.md
- Source: Tag:team
  Matches: "^(payments|billing).*$"

# Regex match multiple patterns
- Source: Tag:description
  Matches:
    - ".* (cost|product) types"
    - "^shared-.*"

# Has any value (non-empty)
- Source: Tag:customer-id
  HasValue: true

# Has no value (empty or missing)
- Source: User:Defined:Product
  HasValue: false

# Multi-source HasValue check
- Sources:
    - User:Defined:Product
    - User:Defined:SharedAtlas
  HasValue: false
```

## Logical Operators

```yaml
# AND — all conditions must be true
- And:
    - Source: Service
      Equals: AmazonS3
    - Source: Tag:app
      BeginsWith: "payments"

# OR — any condition must be true
- Or:
    - Source: Account
      Equals: "111111111111"
    - Source: Account
      Equals: "222222222222"

# NOT — condition must be false
- Not:
    - Source: Tag:env
      Equals: "dev"

# Nested — And/Or/Not can be combined to any depth
- And:
    - Source: CZ:Defined:ResourceSummaryDisplay
      Contains: atlas
    - Or:
        - Source: K8s:Namespace
          BeginsWith: atlas
        - And:
            - Source: Service
              Equals: AWSSecretsManager
            - Source: CZ:Defined:ResourceSummaryDisplay
              BeginsWith: prod-atlas
```

## Multiple Conditions Under a Rule (Implicit OR)

Multiple top-level conditions under a single rule are OR'd — any match assigns the charge to that rule's element:

```yaml
Rules:
  - Type: Group
    Name: Automation
    Conditions:
      - Equals: automation              # matches if dimension-level Sources = automation
      - And:                             # OR matches if Service is CloudWatch AND resource contains automation
          - Source: Service
            Equals: AmazonCloudWatch
          - Source: CZ:Defined:ResourceSummaryDisplay
            Contains: automation
```

## Ordering Conditions

```yaml
# Alphabetical ordering
- Source: Tag:department
  Before: "M"              # matches A-L

- Source: Tag:department
  BeforeOrEquals: "M"      # matches A-M

- Source: Tag:department
  After: "M"               # matches N-Z

- Source: Tag:department
  AfterOrEquals: "M"       # matches M-Z

# Date range filtering (inclusive, uses From/Until)
- ForDateRange:
    From: "2024-01-01"
    Until: "2024-03-31"
```

## CoalesceSources

When using `Sources` (plural), `CoalesceSources: true` picks the first non-null value across all listed sources:

```yaml
- Type: GroupBy
  Sources:
    - K8s:Label:chain.link/team
    - Tag:chain.link/team
    - Tag:team
  CoalesceSources: true
```

## Condition Selection Guide

Prefer in this order for performance:
1. `Equals` — exact, indexed
2. `BeginsWith` / `EndsWith` — prefix/suffix, efficient
3. `Contains` — substring scan, acceptable
4. `Matches` (regex) — row-by-row, Snowflake `REGEXP_LIKE` — last resort only
