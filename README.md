# CloudZero CostFormation Brain

An AI knowledge corpus that makes any coding agent an expert at writing CloudZero CostFormation YAML. Drop it into your project and your AI assistant writes correct, performant definitions on the first try.

Works with Claude Code, Cursor, Copilot, Codex, Windsurf — any IDE or CLI with an AI assistant.

## Quick Start

### 1. Clone the brain into your project

```bash
cd your-project
git clone https://github.com/griffinsisk/costformation-brain.git
```

### 2. Pull your CostFormation file

**VS Code with the CloudZero Toolkit** (`cloudzero.costformation-toolkit`):

The toolkit handles authentication, pulling your latest definition, and publishing changes. If you don't have it yet, install it from the [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=cloudzero.costformation-toolkit).

**Without the toolkit:**

```bash
curl -s -H "Authorization: Bearer $CZ_API_KEY" \
  https://api.cloudzero.com/v1/cost-formation/definitions \
  -o costformation.cz.yaml
```

### 3. Tell your agent about the brain

Copy one instruction file to your project root:

| IDE / CLI | Command |
|---|---|
| Claude Code (CLI or VS Code) | `cp costformation-brain/CLAUDE.md ./CLAUDE.md` |
| Cursor | `cp costformation-brain/.cursorrules ./.cursorrules` |
| GitHub Copilot | `mkdir -p .github && cp costformation-brain/.github/copilot-instructions.md .github/` |
| Codex / Gemini / other | `cp costformation-brain/AGENTS.md ./AGENTS.md` |

**Optional but recommended — Connect the CloudZero MCP:**

The agent works without the MCP (it parses your costformation file directly), but with it connected, the agent can query your accounts, tags, cost data, and dimensions in real-time — producing significantly better output.

- **Claude Code:** Run `/mcp` and add the [CloudZero MCP server](https://docs.cloudzero.com/docs/ai-mcp-server), or install the [CloudZero cost-analyst plugin](https://docs.cloudzero.com/docs/ai-skills) which includes MCP access
- **Cursor / other MCP-enabled agents:** Follow the [MCP setup guide](https://docs.cloudzero.com/docs/ai-mcp-server)

If the MCP isn't connected when you start building, the agent will let you know what it's missing and how to connect it.

### 4. Start building dimensions

```
"Add a Team dimension that maps K8s labels to engineering teams"
```

On first use, the agent automatically:
- Parses your costformation file to extract accounts, tags, dimensions, and source references
- Enriches with CloudZero MCP data if connected (account names, tag coverage, cost drivers)
- Writes the results to `my-org/` and generates a compact `my-org/index.yaml` summary so context persists and loads efficiently across sessions

When you pull a new version of your costformation file, the agent detects the change and refreshes the org context automatically.

Any business context you provide in conversation — team-to-account mappings, CSVs, org charts, goals, constraints — the agent persists to `my-org/context.md` so it's not lost between sessions.

### 5. Publish

**VS Code with the CloudZero Toolkit:** Use the toolkit's built-in publish command.

**Without the toolkit:**

```bash
curl -X POST -H "Authorization: Bearer $CZ_API_KEY" \
  -H "Content-Type: application/yaml" \
  --data-binary @costformation.cz.yaml \
  https://api.cloudzero.com/v1/cost-formation/definitions
```

## How It Works

The instruction file you copied in step 3 forces the agent to read `SKILL.md` before writing any CostFormation YAML. That file contains non-negotiable rules (source prefixes, performance constraints, allocation design) and a routing table that points to 9 corpus files covering syntax, conditions and transforms, telemetry, allocation design, and real-world examples.

The `examples/` directory contains 20 structured CostFormation patterns — from basic account mappings to advanced allocation chains — each with metadata that helps the agent select the right starting point. The agent checks `examples/index.yaml` before writing any dimension from scratch.

The `my-org/` directory stores your org-specific context. It's auto-populated from your costformation file and the CloudZero MCP — you don't need to fill it in manually. The agent refreshes it whenever you pull a new costformation version.

Without the instruction file, agents confidently generate wrong CostFormation syntax from general knowledge. The output looks plausible but uses incorrect structure. The brain fixes this.

## Validator and Eval

The repo includes a CostFormation linter and eval framework. Requires `ruamel.yaml` (`pip install ruamel.yaml`).

```bash
# Lint CostFormation files (11 error rules, 5 warning rules)
python3 validator/lint.py costformation.cz.yaml
python3 validator/lint.py examples/patterns/*.yaml

# Integrity checks (index consistency, anonymization scan)
python3 validator/lint.py --check-integrity

# Run eval cases against golden outputs
python3 evals/run.py --validate-golden
python3 evals/run.py --assert-golden
python3 evals/run.py --list

# Run tests (requires pytest)
python3 -m pytest tests/ -v
```

**Note:** Tests use `pytest`, not `unittest discover`. Install with `pip install pytest`.

## Optional: Connect the CloudZero MCP

The [CloudZero MCP server](https://docs.cloudzero.com/docs/ai-mcp-server) is read-only but significantly enriches the agent's understanding of your environment. With it connected, the agent can query your account's dimensions, costs, tags, and coverage data while writing definitions.

The brain works without the MCP — it parses your costformation file directly — but MCP adds context that isn't in the YAML (account names, tag coverage percentages, cost distribution).

## Reference

| Resource | URL |
|---|---|
| CostFormation Overview | https://docs.cloudzero.com/docs/allocate-through-yaml |
| CostFormation Reference (CFDL) | https://docs.cloudzero.com/docs/cfdl-reference |
| CostFormation Templates | https://docs.cloudzero.com/docs/dimension-patterns |
| Building Dimensions | https://docs.cloudzero.com/docs/dimensions |
| Splitting Shared Costs | https://docs.cloudzero.com/docs/splitting-shared-costs |
| Telemetry Streams | https://docs.cloudzero.com/docs/telemetry-streams |
| Sending Telemetry via API | https://docs.cloudzero.com/docs/send-via-api |
| Telemetry API Reference | https://docs.cloudzero.com/reference/allocation-telemetry-api-1 |
| Unit Economics | https://docs.cloudzero.com/docs/unit-economics |
| Unit Cost Tutorial | https://docs.cloudzero.com/docs/tutorial-calculate-unit-cost-metrics |
| CloudZero MCP Server | https://docs.cloudzero.com/docs/ai-mcp-server |
| CloudZero CostFormation Toolkit (VS Code) | https://marketplace.visualstudio.com/items?itemName=cloudzero.costformation-toolkit |
| Claude Code Skills | https://docs.cloudzero.com/docs/ai-skills |

## Sources

This corpus is built from real CloudZero engineering knowledge and customer implementations:

| What | Source | Used In |
|---|---|---|
| Performance rules, allocation design, DefaultValue guidance, expansion factor formula | CloudZero Engineering — *CostFormation Best Practices* (Confluence, Matt Yellen, Aug 2025) | `performance-rules.md`, `allocation-design.md` |
| 10 worked examples (anonymized) | 12 real customer CostFormation files from the Accounts shared drive | `examples.md` |
| Complete dimension reference (CostFormation syntax, API refs, telemetry filter keys) | *CZ Dimension Reference* spreadsheet | `sources.md`, `telemetry.md` |
| Non-negotiable rules, condition/transform syntax | CFDL language reference + internal engineering tribal knowledge | `SKILL.md`, `conditions-and-transforms.md` |
