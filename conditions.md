# Conditions Reference

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

# Starts with prefix
- Source: UsageType
  StartsWith: "USE2-"

# Begins with (alias for StartsWith)
- Source: User:Defined:AccountName
  BeginsWith: "AWS - Security"

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

# Regex match (Matches) — use sparingly, see performance-rules.md
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
      StartsWith: "payments"

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
  AfterOrEquals: "M"       # matches M-Z

# Date range filtering
- Source: CZ:Defined:BillingLineItem
  ForDateRange:
    Start: "2024-01-01"
    End: "2024-03-31"
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
2. `StartsWith` / `BeginsWith` / `EndsWith` — prefix/suffix, efficient
3. `Contains` — substring scan, acceptable
4. `Matches` (regex) — row-by-row evaluation, no index benefit — last resort only
