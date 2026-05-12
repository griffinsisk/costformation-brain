# File Structure

All Custom Dimensions live in a **single YAML file** called the CostFormation Definition File. All keys nest under the root key `Dimensions`.

```yaml
Dimensions:
  <DimensionId>:        # This IS the dimension's ID for API/CostFormation references
    Name: Human Readable Name
    Hide: false          # Show in Explorer? Default false (visible)
    Disable: false       # Stop computing? Default false
    DefaultValue: Other  # Only set on top-level Explorer dimensions. Omit on hidden/helper dims — see performance-rules.md
    Rules:
      - Name: RuleName
        Value: ElementName
        Conditions:
          - ...
  <DimensionId2>:
    ...
```

## Critical Facts

- `DimensionId` (the YAML key) is used in `Source:` references and the API. The `Name` is display-only.
- The file is **atomic** — you upload the entire file and all dimensions are republished at once. Partial updates are not supported. Always download the current file, modify, and re-upload.
- All dimensions in the file are published simultaneously on upload. Order within the file matters if dimensions reference each other as sources — the referenced dimension must already be published.

## API: Upload / Download

```
# Upload (publish)
POST https://api.cloudzero.com/v1/cost-formation/definitions
Authorization: Bearer <API_KEY>
Content-Type: application/yaml

# Download current file
GET https://api.cloudzero.com/v1/cost-formation/definitions
```
