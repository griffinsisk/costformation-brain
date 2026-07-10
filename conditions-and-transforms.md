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

### And/Or/Not Always Contain a LIST

The value of `And`, `Or`, and `Not` is a **list of conditions** — each item starts with `- `. A bare mapping under the operator is invalid, and the failure mode is nasty: if the malformed clause is rejected or dropped at publish, the surrounding logic silently degrades (e.g. an `And` guard losing its `Not` exclusion matches far more spend than intended).

```yaml
# ❌ Incorrect — bare mapping under Not
- Not:
    Source: User:Defined:Customer
    Equals: "Other"

# ✅ Correct — list of conditions under Not
- Not:
    - Source: User:Defined:Customer
      Equals: "Other"
```

`Not` evaluates its list as a logical Or, then negates the result.

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

---

## Formatting Conventions

Style rules for writing consistent, reviewable CostFormation YAML. Apply these when authoring new definitions or cleaning up existing ones.

---

### Parameter Ordering

Use a fixed parameter order within each block. This makes diffs readable and avoids hunting for fields.

**Dimension header:** `Name` → `Disable` → `Hide` → `Child` → `Source` / `Sources` → `Transforms` → `DefaultValue`

**Condition block:** `Source` / `Sources` → `Transforms` → conditional operator (`Equals`, `BeginsWith`, etc.)

**GroupBy rule:** `Type` → `Source` / `Sources` → `Transforms` → `Format` (concatenation only) → `CoalesceSources` (coalescing only) → `Conditions`

```yaml
# ✅ Correct — parameters in prescribed order
- Id: environment
  Name: Environment
  Hide: true
  Source: Tag:environment
  Transforms:
    - Type: Lower
  DefaultValue: Unknown
  Rules:
    - Type: Group
      Name: Production
      Conditions:
        - Source: Tag:environment
          Transforms:
            - Type: Lower
          Equals: prod
```

```yaml
# ❌ Incorrect — arbitrary order makes diffs noisy
- Id: environment
  DefaultValue: Unknown
  Rules:
    - Type: Group
      Conditions:
        - Equals: prod
          Source: Tag:environment
          Transforms:
            - Type: Lower
      Name: Production
  Transforms:
    - Type: Lower
  Source: Tag:environment
  Name: Environment
  Hide: true
```

---

### Value Formatting

**Single value:** write inline on the same line as the operator.

```yaml
# ✅ Correct
Equals: prod
BeginsWith: "payments-"
```

```yaml
# ❌ Incorrect — unnecessary block for a single value
Equals:
  - prod
```

**Multiple values:** use collapsed inline array notation, alphabetized case-insensitively, with a newline after every 5th value.

```yaml
# ✅ Correct — collapsed, alphabetized, line-wrapped at 5
Equals: [analytics, billing, data, fintech, infra,
         payments, platform, security, shared]
```

```yaml
# ❌ Incorrect — expanded block list when no inline comments are needed
Equals:
  - payments
  - billing
  - analytics
  - infra
  - data
  - platform
```

**Exception:** preserve expanded format when any value carries an inline comment.

```yaml
# ✅ Correct — expanded because one value needs a comment
Equals:
  - payments
  - billing   # includes legacy billing-v1 accounts
  - analytics
```

**Source field:** single source inline; multiple sources as a block list or array.

```yaml
# ✅ Correct — single source inline
Source: Tag:environment

# ✅ Correct — multiple sources as block list
Sources:
  - Tag:environment
  - Tag:env
  - K8s:Label:environment
```

```yaml
# ❌ Incorrect — single source as a one-element array
Sources:
  - Tag:environment
```

---

### Source Shorthand (Dimension-Level Promotion)

When more than 50% of rules in a dimension share the same source, promote it to the dimension header instead of repeating it on every condition.

**This shorthand applies to `Group` rule conditions only.** A `Type: GroupBy` rule must always declare its own `Source`/`Sources` (plus `Transforms`/`CoalesceSources` when used) on the rule itself — a bare `- Type: GroupBy` relying on the dimension header is invalid, even when the dimension's only rule is the GroupBy.

```yaml
# ❌ Incorrect — bare GroupBy relying on dimension-level source
- Id: team
  Name: Team
  Source: Tag:team
  Transforms:
    - Type: Lower
  Rules:
    - Type: GroupBy

# ✅ Correct — GroupBy carries its own source and transforms
- Id: team
  Name: Team
  Rules:
    - Type: GroupBy
      Source: Tag:team
      Transforms:
        - Type: Lower
```

In mixed dimensions (Group rules + a GroupBy passthrough), keep the dimension-level source for the Group rules and repeat it explicitly on the GroupBy rule.

```yaml
# ✅ Correct — source declared once at dimension level
- Id: team
  Name: Team
  Source: Tag:team
  Rules:
    - Type: Group
      Name: Payments
      Conditions:
        - Equals: payments
    - Type: Group
      Name: Platform
      Conditions:
        - Equals: platform
    - Type: Group
      Name: Data
      Conditions:
        - Equals: data
```

```yaml
# ❌ Incorrect — source repeated on every condition when it never varies
- Id: team
  Name: Team
  Rules:
    - Type: Group
      Name: Payments
      Conditions:
        - Source: Tag:team
          Equals: payments
    - Type: Group
      Name: Platform
      Conditions:
        - Source: Tag:team
          Equals: platform
    - Type: Group
      Name: Data
      Conditions:
        - Source: Tag:team
          Equals: data
```

Note: Override the dimension-level source on individual conditions only when a specific rule needs a different source.

---

### Section Comments

Use dashed comment blocks to separate logical sections within a dimension file. Keep comment lines to a consistent width.

```yaml
# ✅ Correct — dashed separator before each logical section
#--------------------------------------------
# Environment Dimensions
#--------------------------------------------
- Id: environment
  Name: Environment
  ...

#--------------------------------------------
# Team / Ownership Dimensions
#--------------------------------------------
- Id: team
  Name: Team
  ...
```

```yaml
# ❌ Incorrect — blank lines or free-form comments as separators
# Environment
- Id: environment
  ...

# team stuff
- Id: team
  ...
```

---

### Cleanup Rules

Apply these when reviewing or refactoring existing definitions.

**No blank lines between rules within the same dimension.** Blank lines between dimensions are fine; blank lines between sibling rules inside one dimension add noise.

```yaml
# ✅ Correct — no blank lines between rules
Rules:
  - Type: Group
    Name: Production
    Conditions:
      - Equals: prod
  - Type: Group
    Name: Staging
    Conditions:
      - Equals: staging
```

```yaml
# ❌ Incorrect — blank lines between sibling rules
Rules:
  - Type: Group
    Name: Production
    Conditions:
      - Equals: prod

  - Type: Group
    Name: Staging
    Conditions:
      - Equals: staging
```

**Quote names — and string values that reference them — containing YAML special characters** (`:`, `#`, `{`, `}`, `[`, `]`, `*`, `&`, `!`, `|`, `>`, `'`, `"`, `%`, `@`, `` ` ``). This applies to `Name:` and equally to condition values that reference such an element, e.g. `Equals: "Other (Internal & Unclassified)"`.

```yaml
# ✅ Correct
Name: "Cost: Shared Infrastructure"
Name: "R&D"
```

```yaml
# ❌ Incorrect — unquoted YAML special characters
Name: Cost: Shared Infrastructure
Name: R&D
```

**Account IDs are always quoted strings, left-padded to 12 digits.**

```yaml
# ✅ Correct
Equals: "012345678901"
```

```yaml
# ❌ Incorrect — unquoted or unpadded
Equals: 12345678901
Equals: "12345678901"
```

**Strip `Hide: false` and `Disable: false`.** Both are implicit defaults; writing them adds clutter.

```yaml
# ✅ Correct — implicit defaults omitted
- Id: team
  Name: Team
  Source: Tag:team
```

```yaml
# ❌ Incorrect — explicit false adds noise
- Id: team
  Name: Team
  Hide: false
  Disable: false
  Source: Tag:team
```

**Consider `Child: Service`** for visible top-level grouping dimensions (e.g., Team, Product, Environment) unless a different drill-down is more useful. `Child: Service` gives users a one-click path to see which AWS/GCP services are driving cost within each element, which is the most common follow-up question.

```yaml
# ✅ Correct — Child declared for a top-level grouping dimension
- Id: team
  Name: Team
  Child: Service
  Source: Tag:team
```

**Strip trailing whitespace** from all lines before committing.
