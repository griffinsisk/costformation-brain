# Conditions Reference

## Basic Conditions

```yaml
# Exact match (case-sensitive by default)
- Match:
    Source: Account
    Value: "123456789012"

# Match multiple values (OR semantics within the same Match)
- Match:
    Source: Service
    Values:
      - AmazonEC2
      - AmazonRDS

# Starts with prefix
- StartsWith:
    Source: UsageType
    Value: "USE2-"

# Ends with suffix
- EndsWith:
    Source: Tag:env
    Value: "-prod"

# Contains substring
- Contains:
    Source: CZ:Defined:ResourceSummaryDisplay
    Value: "payments"

# Regex match — use sparingly, see performance-rules.md
- Regex:
    Source: Tag:team
    Pattern: "^(payments|billing).*$"

# Tag exists (has any non-empty value)
- Exists:
    Source: Tag:customer-id
```

## Logical Operators

```yaml
# AND — all conditions must be true
- And:
    - Match:
        Source: Service
        Value: AmazonS3
    - StartsWith:
        Source: Tag:app
        Value: "payments"

# OR — any condition must be true
- Or:
    - Match:
        Source: Account
        Value: "111111111111"
    - Match:
        Source: Account
        Value: "222222222222"

# NOT — condition must be false
- Not:
    - Match:
        Source: Tag:env
        Value: "dev"
```

## Condition Selection Guide

Prefer in this order for performance:
1. `Match` — exact, indexed
2. `StartsWith` / `EndsWith` — prefix/suffix, efficient
3. `Contains` — substring scan, acceptable
4. `Regex` — row-by-row evaluation, no index benefit — last resort only
