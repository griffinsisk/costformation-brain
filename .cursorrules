When writing, reviewing, or debugging CloudZero CostFormation YAML:

1. Always read `costformation-brain/SKILL.md` first — it contains non-negotiable rules and a routing table to the full knowledge corpus.
2. Auto-populate org context — see rules below. Do this before writing any definition.
3. Always read all files in `costformation-brain/my-org/` before writing any definition.
4. Always read `costformation-brain/performance-rules.md` before generating any dimension definition.
5. Always read `costformation-brain/allocation-design.md` before writing any Allocation Dimension.
6. Consult the relevant corpus file from `costformation-brain/` based on the task — the routing table in SKILL.md tells you which file to read.

Do NOT write CostFormation YAML from memory or general knowledge. The corpus contains CloudZero-specific syntax, performance rules from the engineering team that maintains Snowflake, and real-world patterns. General YAML knowledge will produce syntactically plausible but incorrect output.

## Auto-Populate Org Context

Before writing any CostFormation, check whether `costformation-brain/my-org/` needs to be populated or refreshed:

Populate if empty: If accounts.yaml, tags.yaml, or dimensions.yaml contain only comments or empty arrays, auto-populate them:
1. Parse the costformation definition file (.cz.yaml or .yaml) in the workspace — extract all accounts, tag sources, dimension IDs/types/names, and source references.
2. If the CloudZero MCP is connected, enrich with: account names, tag coverage, cost drivers, and any dimensions not in the YAML.
3. Write the results into the my-org/ files and update the `# last-synced:` header with the current ISO timestamp.

Refresh if stale: If the costformation definition file has a more recent modification time than the `# last-synced` timestamp in the my-org/ files, re-populate by repeating the steps above.

Never overwrite context.md. That file contains business context provided by the user. Only append to it, never replace.

## Use Data Before Asking Questions

When the user asks you to create or modify a dimension, do NOT ask questions the data can answer. Instead:

1. Query the CloudZero MCP first (if connected) — pull accounts, tags, existing dimensions, cost data, tag coverage. Look at what's actually in the environment.
2. Parse the costformation file — see what dimensions already exist, what sources and patterns are used, what naming conventions are in place.
3. Read `costformation-brain/my-org/` — check for any persisted org context from prior sessions.
4. Infer the answer from the data. If the user asks for an "Environment dimension," look for environment-related tags (env, environment, Environment), account naming patterns, and existing dimension references. Build the dimension from what you find.
5. Only ask the customer what the data can't tell you. Team ownership, business goals, how shared costs should be split — these require human input. Account IDs, tag keys, and naming patterns do not.

Present what you built with a brief explanation of what you found in the data. The customer confirms or adjusts — they shouldn't have to teach the agent things the MCP already knows.

## Persist Business Context

When the user provides org context during conversation — team-to-account mappings, CSVs, org charts, business rules, constraints, or goals — write it to `costformation-brain/my-org/context.md` so it's available in future sessions. Append new context under the relevant section heading. Do not lose information between sessions.
