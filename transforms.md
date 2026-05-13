# Transforms Reference

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

## Available Transforms

| Transform | Effect | Example |
|---|---|---|
| `Lower` | Converts to lowercase | `ProductionResource 1` → `productionresource 1` |
| `Upper` | Converts to uppercase | `the cost types` → `THE COST TYPES` |
| `Title` | Capitalizes first letter of each word | `the cost types` → `The Cost Types` |
| `Trim` | Removes leading/trailing whitespace | `" the cost types "` → `"the cost types"` |
| `Clean` | Removes whitespace, converts `.,/#!$%^&*;:=_~()\'` and spaces to dashes | `" The:Cost!Types "` → `"The-Cost-Types"` |
| `Normalize` | Combines Lower + Trim + special-char conversion | `Production/Resources#4561` → `production-resources-4561` |
| `Split` | Splits on delimiter, extracts Nth part (**1-based index**) | See below |

## Examples

### Lower — normalize inconsistent tag values
```yaml
Transforms:
  - Type: Lower
```

### Normalize — clean and lowercase in one step
```yaml
Transforms:
  - Type: Normalize
```

### Split — extract a segment from a delimited string

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

### Chaining transforms — execute in order
```yaml
Transforms:
  - Type: Lower
  - Type: Trim
```

## When to Use Transforms

- **Always use `Lower`** when matching user-applied tags — tagging is rarely consistent across teams
- Use `Normalize` when tag values have mixed casing AND special characters
- Use `Split` to extract parts from composite values rather than writing multiple `Equals` conditions
- Prefer transforms over writing duplicate rules for casing variants
