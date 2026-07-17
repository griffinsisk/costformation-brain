# Customer Build Profile

## Session Initialization

1. Read `SKILL.md` and complete its startup checks.
2. Read `workspace/two-file-workflow.md`.
3. Inventory optional MCPs using `connectors/discovery.md`.
4. Validate `.costformation/capabilities.yaml` when it exists.
5. Index customer-provided files under `context/provided/` without moving or
   copying their contents into `costformation-brain/`.
6. Read distilled evidence according to `evidence/authority.md` and re-query
   anything stale.

## Build Flow

1. Query the CloudZero MCP first when creating or modifying a dimension.
2. Parse the immutable `costformation.cz.yaml` baseline.
3. Decompose the requested concept into tags, accounts, resource names,
   Kubernetes signals, existing dimensions, and relevant optional capabilities.
4. Query independent readable sources in parallel.
5. Normalize findings as observed, customer-confirmed, inferred, conflicting,
   or stale; never silently upgrade an inference.
6. Ask only for business meaning or choices the available evidence cannot
   answer.
7. Build the complete `costformation.proposed.cz.yaml`.
8. Validate with `validator/workspace_check.py` and fix all errors.
9. Present an evidence-coverage summary, concise diff, and warnings.
10. Stop. The user publishes through the CloudZero VS Code Toolkit.

## External Actions

Use available read-only tools when relevant. Never invoke a write-capable or
ambiguous external tool without explicit approval for that specific action.

## Persistence

Persist only distilled customer evidence with provenance. Never persist raw
transcripts, complete tool responses, or credentials. Never write customer
artifacts inside the `costformation-brain` repository and never promote them to
shared knowledge automatically.
