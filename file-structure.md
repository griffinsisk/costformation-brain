# File Structure

All Custom Dimensions live in a **single YAML file** called the CostFormation Definition File. All keys nest under the root key `Dimensions`.

```yaml
Dimensions:
  <DimensionId>:                          # This IS the dimension's ID for Source references and API
    Name: Human Readable Name             # Display name in Explorer (optional, defaults to DimensionId)
    Type: Grouping                        # Grouping (default) or Allocation
    Hide: false                           # Hide from Explorer but allow as source? (default: false)
    Disable: false                        # Stop computing entirely? (default: false)
    DefaultValue: Other                   # Only on top-level Explorer dims — see performance-rules.md
    Child: Service                        # Next drill-down dimension in Explorer (optional)
    Override: CZ:Defined:<DimensionId>    # Replace a built-in CZ dimension (optional)
    Source: Account                       # Default source inherited by all rules (optional)
    CoalesceSources: false                # Use first non-null source (optional)
    Transforms:                           # Default transforms inherited by all rules (optional)
      - Type: Lower
    Rules:
      - Type: Group                       # Required: Group, GroupBy, or Metadata
        Name: ElementName
        Conditions:
          - Equals: "value"

  # Allocation dimension example
  <AllocationDimId>:
    Type: Allocation
    Name: Split Shared Costs
    AllocateByRules:                      # or AllocateByStreams
      AllocationMethod: Proportional      # Proportional, Even, or Fixed
      SpendToAllocate:
        Conditions:
          - Source: Service
            Equals: AmazonRDS
      AcrossElements:
        GroupBy:
          Source: User:Defined:Product
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
