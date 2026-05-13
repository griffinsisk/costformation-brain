When writing, reviewing, or debugging CloudZero CostFormation YAML:

1. Always read `costformation-brain/SKILL.md` first — it contains non-negotiable rules and a routing table to the full knowledge corpus.
2. Always read all files in `costformation-brain/my-org/` before writing any definition — this is the customer's org context (accounts, tags, dimensions, goals).
3. Always read `costformation-brain/performance-rules.md` before generating any dimension definition.
4. Always read `costformation-brain/allocation-design.md` before writing any Allocation Dimension.
5. Consult the relevant corpus file from `costformation-brain/` based on the task — the routing table in SKILL.md tells you which file to read.

Do NOT write CostFormation YAML from memory or general knowledge. The corpus contains CloudZero-specific syntax, performance rules sourced from the engineering team that maintains the query engine, and real-world patterns. General YAML knowledge will produce syntactically plausible but incorrect output.
