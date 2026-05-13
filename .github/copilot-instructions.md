When writing, reviewing, or debugging CloudZero CostFormation YAML:

1. Always read `costformation-brain/SKILL.md` first — it contains non-negotiable rules and a routing table to the full knowledge corpus.
2. Check if `costformation-brain/my-org/` needs updating — see the freshness rules below.
3. Always read all files in `costformation-brain/my-org/` before writing any definition — this is the customer's org context.
4. Always read `costformation-brain/performance-rules.md` before generating any dimension definition.
5. Always read `costformation-brain/allocation-design.md` before writing any Allocation Dimension.
6. Consult the relevant corpus file from `costformation-brain/` based on the task — the routing table in SKILL.md tells you which file to read.

Do NOT write CostFormation YAML from memory or general knowledge. The corpus contains CloudZero-specific syntax, performance rules sourced from the engineering team that maintains the query engine, and real-world patterns. General YAML knowledge will produce syntactically plausible but incorrect output.

## Auto-Populate Org Context

Before writing any CostFormation, check whether `costformation-brain/my-org/` needs to be populated or refreshed:

Populate if empty: If accounts.yaml, tags.yaml, or dimensions.yaml contain only comments (no actual data), auto-populate them:
1. Parse the costformation definition file (.cz.yaml or .yaml) in the workspace — extract all accounts, tag sources, dimension IDs/types/names, and source references.
2. If the CloudZero MCP is connected, enrich with: account names, tag coverage, cost drivers, and any dimensions not in the YAML.
3. Write the results into the my-org/ files using the template format, and add a `# last-synced: <ISO timestamp>` header to each file.

Refresh if stale: If the costformation definition file has a more recent modification time than the `# last-synced` timestamp in the my-org/ files, re-populate by repeating the steps above.

Never overwrite context.md. That file contains business context provided by the user. Only append to it, never replace.

## Persist Business Context

When the user provides org context during conversation — account-to-team mappings, org charts, CSVs, tag conventions, business rules, constraints, or goals — write it to `costformation-brain/my-org/context.md` so it's available in future sessions. Append new context under the relevant section heading. Do not lose information between sessions.
