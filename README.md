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

The toolkit handles authentication, pulling your latest definition, and publishing changes — no API key in the terminal needed. If you don't have it yet, install it from the [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=cloudzero.costformation-toolkit).

**Without the toolkit:**

```bash
curl -s -H "Authorization: Bearer $CZ_API_KEY" \
  https://api.cloudzero.com/v1/cost-formation/definitions \
  -o costformation.cz.yaml
```

### 3. Tell your agent about the brain

Agents won't read local files on their own — they need to be told. Copy the instruction file for your IDE to the project root:

| IDE / CLI | Command |
|---|---|
| Claude Code (CLI or VS Code) | `cp costformation-brain/CLAUDE.md ./CLAUDE.md` |
| Cursor | `cp costformation-brain/.cursorrules ./.cursorrules` |
| GitHub Copilot | `mkdir -p .github && cp costformation-brain/.github/copilot-instructions.md .github/` |
| Codex / Gemini / other | `cp costformation-brain/AGENTS.md ./AGENTS.md` |

### 4. (Optional) Add your org context

The `my-org/` directory has templates for your accounts, tags, existing dimensions, and goals. Filling these in is the difference between generic output and output that uses your actual infrastructure.

| File | What to put in it |
|---|---|
| `my-org/accounts.yaml` | AWS account IDs, names, owners, department/team mapping |
| `my-org/tags.yaml` | Tag keys your teams use, naming conventions, coverage gaps |
| `my-org/dimensions.yaml` | Existing dimensions + dimensions you want to build |
| `my-org/context.md` | Business structure, cost views you need, constraints |

Each file has a commented template — fill in what's relevant, skip what isn't. Even partial context (just your account list) significantly improves output.

If you have the [CloudZero MCP server](https://docs.cloudzero.com/docs/ai-mcp-server) connected, you can ask the agent to populate these from your account automatically — then add the business context the API can't know (team ownership, dimension goals, how shared costs should be split).

### 5. Start building dimensions

Open your project in VS Code (or your IDE of choice) and talk to your coding agent:

```
"Add a Team dimension that maps K8s labels to engineering teams"
```

The agent reads the brain, checks your org context, and generates correct CostFormation YAML directly in your definition file.

### 6. Publish

**VS Code with the CloudZero Toolkit:** Use the toolkit's built-in publish command — it handles diff review and conflict resolution.

**Without the toolkit:**

```bash
curl -X POST -H "Authorization: Bearer $CZ_API_KEY" \
  -H "Content-Type: application/yaml" \
  --data-binary @costformation.cz.yaml \
  https://api.cloudzero.com/v1/cost-formation/definitions
```

## How It Works

The instruction file you copied in step 3 forces the agent to read `SKILL.md` before writing any CostFormation YAML. That file contains non-negotiable rules (source prefixes, performance constraints, allocation design) and a routing table that points to 10 corpus files covering syntax, conditions, transforms, telemetry, allocation design, and real-world examples.

The `my-org/` directory provides your org-specific context. The agent reads everything on demand — not all at once — so context window usage stays efficient.

Without the instruction file, agents confidently generate wrong CostFormation syntax from general knowledge. The output looks plausible but uses incorrect structure. The brain fixes this.

## Reference

| Resource | URL |
|---|---|
| CostFormation Overview | https://docs.cloudzero.com/docs/cost-formation-definition-language |
| CFDL Guide | https://docs.cloudzero.com/docs/costformation-definition-language-guide |
| CFDL Language Reference | https://docs.cloudzero.com/docs/cfdl-reference |
| Allocation Short Form Rules | https://docs.cloudzero.com/docs/allocation-short-form-rules |
| Allocating Shared Costs | https://docs.cloudzero.com/docs/costformation-allocating-shared-costs |
| Telemetry API Reference | https://docs.cloudzero.com/reference/allocation-telemetry-api-1 |
| Advanced Dimension Features | https://docs.cloudzero.com/docs/ds-advanced-features |
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
| Non-negotiable rules, condition/transform syntax | CFDL language reference + internal engineering tribal knowledge | `SKILL.md`, `conditions.md`, `transforms.md` |
