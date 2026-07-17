# Optional MCP discovery

Treat every customer MCP as an optional capability. Do not assume a particular vendor, server name, or installed connector.

1. Inventory the MCP servers and tools available in the current session.
2. Classify useful servers by the capability categories in `connectors/capability-model.yaml`.
3. Mark access as `read-only`, `write-capable`, or `ambiguous`. When access is unclear, use `ambiguous`.
4. Auto-select only capabilities that are both available and read-only. Any write-capable or ambiguous tool requires explicit customer approval before use.
5. Persist only the capability classification in `.costformation/capabilities.yaml`. Never persist credentials, tokens, raw tool responses, or customer secrets.
6. Validate the manifest with `python3 costformation-brain/validator/capability_check.py .costformation/capabilities.yaml`.

An unavailable capability is a documented evidence gap, not a setup failure. Continue with the local CostFormation file and other read-only sources, and clearly label any resulting inference or unresolved question.
