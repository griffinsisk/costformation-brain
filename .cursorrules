When writing, reviewing, or debugging CloudZero CostFormation YAML:

1. Always read `costformation-brain/SKILL.md` first — it contains non-negotiable rules and a routing table to the full knowledge corpus.
2. Auto-populate org context — see rules below. Do this before writing any definition.
3. Read `my-org/index.yaml` first for a compact summary, then `my-org/context.md` (always). Load full my-org/ detail files only when you need specifics. For new writes, load all detail files if the index is empty, stale, or missing relevant signals.
4. Always read `costformation-brain/performance-rules.md` before generating any dimension definition.
5. Always read `costformation-brain/allocation-design.md` before writing any Allocation Dimension.
6. Consult the relevant corpus file from `costformation-brain/` based on the task — the routing table in SKILL.md tells you which file to read.
7. Check `costformation-brain/examples/index.yaml` for a matching pattern before writing a dimension from scratch.

After generating or modifying CostFormation YAML, validate before presenting:
- Run `python3 costformation-brain/validator/lint.py <file>` on the generated output.
- Fix all ERRORs before showing the YAML. Do not present YAML that has validator errors.
- Briefly summarize any remaining WARNINGs when presenting. Do not block on warnings.

Do NOT write CostFormation YAML from memory or general knowledge. The corpus contains CloudZero-specific syntax, performance rules from the engineering team that maintains Snowflake, and real-world patterns. General YAML knowledge will produce syntactically plausible but incorrect output.

## Pre-Generation Checklist

Before writing ANY CostFormation YAML, state what you read and why. Include a brief summary:

- Corpus files read: which files and why
- my-org/index.yaml — [summary: account count, dimension count, has_k8s, top signals]
- my-org/context.md — [business context found, or "empty"]
- Detail files loaded: [which ones and why, or "index was empty, loaded all"]
- Data sources checked: MCP connected? Costformation file parsed? Which signal sources for this dimension?

This makes compliance observable. If you skip a file, the gap is visible.

## Auto-Populate Org Context

Before writing any CostFormation, check whether workspace-root `my-org/` needs to be populated or refreshed:

Populate if empty: If accounts.yaml, tags.yaml, or dimensions.yaml contain only comments or empty arrays (last-synced: never), auto-populate them:
1. Parse the costformation definition file (.cz.yaml or .yaml) in the workspace — extract all accounts, tag sources, dimension IDs/types/names, and source references.
2. If the CloudZero MCP is connected, enrich with: account names, tag coverage, cost drivers, and any dimensions not in the YAML.
3. Write the results into the my-org/ files and update the `# last-synced:` header with the current ISO timestamp.
4. Compute a hash of the costformation file and write it as `# source-hash: <sha256>` in each my-org/ file.
5. Generate/refresh `my-org/index.yaml` with counts, top signals, and a `context-hash` (sha256 of `my-org/context.md`).

Refresh if stale: Compare the current costformation file's sha256 hash against the `# source-hash:` in the my-org/ files. If they differ, the costformation file has changed — re-populate by repeating the steps above.

Never overwrite context.md. That file is append-only. See the guard at the top of the file.

## Onboarding Journey

A guided, resumable onboarding path lives at `costformation-brain/onboarding/journey.md`.
- Offer it once when the costformation file has fewer than 3 custom dimensions and `my-org/onboarding-state.yaml` shows no prior offer or decline.
- On every session start, check `my-org/onboarding-state.yaml` for `waiting-external` entries past their `verify-after` date and surface them ("telemetry verification for stream X is overdue — check it now?"). This check is independent of the offer condition.
- Enter or resume on "onboard", "suggest dimensions", "continue onboarding", or "where were we" — journey.md has the resume-reconciliation rules.

## Always Query MCP First

When the user asks you to create or modify a dimension, always query the CloudZero MCP — even if you already have a CSV, an existing costformation file, or prior context. The MCP is a cross-reference, not a fallback. It catches accounts the CSV missed, tags the file doesn't show, and dimensions that exist in CloudZero but not in the local YAML.

1. Query the CloudZero MCP first (if connected) — pull accounts, tags, existing dimensions, cost data, tag coverage. Do this even if the user provided a CSV or you already parsed the costformation file. Cross-reference MCP data against other sources to find gaps.
2. Parse the costformation file — see what dimensions already exist, what sources and patterns are used, what naming conventions are in place.
3. Read `my-org/index.yaml` first, then `my-org/context.md` — check for persisted org context from prior sessions. Load detail files if the index is missing signals you need.
4. Check ALL signal sources for the concept the user is asking about. Don't just look at tags. For any dimension, check:
   - Tags — look for relevant tag keys and their values
   - Account names — accounts often contain environment, team, or product signals in their names (e.g., aws-prod-app-001, ENTERPRISE-DEV, staging-data)
   - Resource names — query CZ:Defined:ResourceSummaryDisplay for patterns matching the concept (e.g., -prod, -dev, staging). Many resources encode environment, team, or product in their names but lack tags. Only add as a condition when the query returns matches that tags and accounts don't already cover — don't add resource name patterns just for redundancy
   - K8s labels and namespaces — workloads, namespaces, and labels frequently encode environment, team, or product
   - Existing dimensions — other dimensions may already classify the concept you need
5. Build the dimension for maximum coverage with minimum verbosity. Use every signal that adds coverage — but don't add redundant conditions. If tags and accounts already catch all charges for an element, skip resource name patterns. If resources carry signals that tags miss, add them. The goal is no uncovered spend, not maximum conditions.
6. Only ask the customer what the data can't tell you. Team ownership, business goals, how shared costs should be split — these require human input. Account IDs, tag keys, resource patterns, and naming conventions do not.

Do not set DefaultValue unless the user specifically asks for a named catch-all bucket. CostFormation defaults to "Not in Dimension" which is sufficient.

Present what you built with a brief explanation of what you found in the data. The customer confirms or adjusts — they shouldn't have to teach the agent things the MCP already knows.

## Persist Business Context

When the user provides org context during conversation — team-to-account mappings, CSVs, org charts, business rules, constraints, or goals — append it to `my-org/context.md` under the relevant section heading. Do not lose information between sessions. Never replace existing content — only add to it.

Customer-specific documents, `my-org/`, `context/`, `.costformation/`, and both
CostFormation definition files live in the customer workspace outside the
`costformation-brain` repository. Never write customer data inside either Git
repository.

## Two-File CostFormation Workflow

Always read `costformation-brain/workspace/two-file-workflow.md` before changing
CostFormation.

For the customer-safe build workflow, read
`costformation-brain/profiles/customer.md`. It routes optional MCP discovery,
evidence reconciliation, the complete proposal build, and validation.

- Never edit `costformation.cz.yaml`; it is the latest downloaded baseline.
- Make changes only in the complete `costformation.proposed.cz.yaml` file.
- If an existing proposal differs from the baseline, ask whether to retain,
  replace, or rebase it. Never overwrite it silently.
- Validate with `python3 costformation-brain/validator/workspace_check.py .`
  before handoff.
- Never publish; the user publishes through the CloudZero VS Code Toolkit.

## NEVER

- Write bare `Source: <DimensionId>` for custom or CZ dimensions without a prefix — `User:Defined:` and `CZ:Defined:` prefixes are required. Core billing sources (`Account`, `Service`, `Region`, etc.) are bare
- Edit `costformation.cz.yaml` or publish CostFormation on the user's behalf
