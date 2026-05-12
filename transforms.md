# Transforms Reference

Transforms mutate source values **before** conditions evaluate them. They are applied at the rule level.

```yaml
Rules:
  - Name: NormalizeEnv
    Value: Production
    Conditions:
      - Match:
          Source: Tag:environment
          Value: prod
    Transforms:
      - Type: Lowercase   # source value lowercased before matching
```

## Available Transforms

| Transform | Effect |
|---|---|
| `Lowercase` | Converts entire value to lowercase |
| `Split` | Splits on a delimiter, extracts the Nth part (0-based index) |
| `Regex.Extract` | Extracts a named or indexed regex capture group |
| `Replace` | Substitutes a substring with another value |

## Examples

### Lowercase — normalize inconsistent tag values
```yaml
Transforms:
  - Type: Lowercase
```

### Split — extract first segment of a `team/subteam` tag
```yaml
Transforms:
  - Type: Split
    Delimiter: "/"
    Index: 0    # extracts "payments" from "payments/backend"
```

### Regex.Extract — pull environment from a composite tag
```yaml
Transforms:
  - Type: Regex.Extract
    Pattern: "^.*-(?P<env>prod|staging|dev)$"
    Group: env
```

## When to Use Transforms

- **Always use `Lowercase`** when matching user-applied tags — tagging is rarely consistent across teams
- Use `Split` to normalize composite tag values rather than writing multiple `Match` conditions
- Prefer transforms over writing duplicate rules for casing variants
