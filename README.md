# CloudZero CostFormation Brain

An AI knowledge corpus that makes any coding agent an expert at writing CloudZero CostFormation YAML. Drop it next to your dimension file and your AI assistant writes correct, performant definitions on the first try.

Works with Claude Code, Cursor, Copilot, Codex, Windsurf — any IDE or CLI with an AI assistant that reads local context.

## Quick Start

### 1. Pull your current CostFormation file

```bash
curl -s -H "Authorization: Bearer $CZ_API_KEY" \
  https://api.cloudzero.com/v1/cost-formation/definitions \
  -o costformation.cz.yaml
```

### 2. Drop the brain next to it

```bash
# Clone into the same directory as your dimension file
git clone https://github.com/cloudzero/costformation-brain.git

# Your workspace should look like this:
# my-costformation/
#   costformation.cz.yaml        ← your dimension file
#   costformation-brain/          ← this repo
#     SKILL.md
#     concepts.md
#     examples.md
#     ...
```

Or download and unzip — no git required.

### 3. Start editing

Open the folder in your IDE or CLI and ask your AI assistant to work on the dimension file. It automatically picks up the corpus and applies the rules.

**Claude Code:**
```bash
cd my-costformation
claude
# "Add a Team dimension that maps K8s labels to engineering teams"
```

**Cursor / Copilot / Windsurf:**
Open the folder. The AI reads SKILL.md from the local context and uses the corpus files when generating CostFormation YAML.

**Codex CLI:**
```bash
cd my-costformation
codex
# Same as above — local files are picked up as context
```

### 4. Upload your changes

```bash
curl -X POST -H "Authorization: Bearer $CZ_API_KEY" \
  -H "Content-Type: application/yaml" \
  --data-binary @costformation.cz.yaml \
  https://api.cloudzero.com/v1/cost-formation/definitions
```

## What's Inside

```
SKILL.md                 ← Agent entry point — non-negotiable rules and corpus routing
concepts.md              ← Core terminology, mental model, design principles
file-structure.md        ← YAML skeleton and file conventions
sources.md               ← Source prefixes and available source IDs
conditions.md            ← All condition types with examples
transforms.md            ← All transform types with examples
dimension-types.md       ← Standard, Child, and Allocation dimension types
allocation-design.md     ← Allocation-specific design rules and anti-patterns
telemetry.md             ← Telemetry API, stream design, target dimensions
performance-rules.md     ← Snowflake cost rules — the agent reads this before every definition
examples.md              ← 10 real-world-derived worked examples
my-org/                  ← YOUR org context — accounts, tags, dimensions, goals
  accounts.yaml          ← AWS account IDs, names, owners, department mapping
  tags.yaml              ← Tag keys in use, naming conventions, coverage notes
  dimensions.yaml        ← Existing dimensions + what you want to build
  context.md             ← Business structure, goals, constraints (freeform)
```

## How It Works

Your AI assistant reads `SKILL.md` as its entry point. That file contains:
- **Non-negotiable rules** the agent must always follow (source prefixes, performance constraints, allocation design rules)
- **A routing table** that tells the agent which corpus file to consult for each type of task

The corpus files contain the actual knowledge — syntax references, worked examples, anti-patterns sourced from CloudZero's engineering team and real customer implementations. The `my-org/` directory provides your org-specific context — accounts, tags, existing dimensions, and goals. The agent reads these on demand, not all at once, so context window usage stays efficient.

## Customize for Your Org

The `my-org/` directory is where you provide context about **your** environment. The agent reads these files before writing any dimension — it's the brief that makes the output match your infrastructure.

| File | What to put in it |
|---|---|
| `accounts.yaml` | AWS account IDs, names, owners, department/team mapping |
| `tags.yaml` | Tag keys your teams use, naming conventions, coverage gaps |
| `dimensions.yaml` | Existing dimensions + dimensions you want to build |
| `context.md` | Business structure, cost views you need, constraints, preferences |

Each file has a commented template — fill in what's relevant, skip what isn't.

### Auto-populate from CloudZero MCP

If you have the [CloudZero MCP server](https://docs.cloudzero.com/docs/ai-mcp-server) connected, ask your agent:

```
Populate my-org/ from my CloudZero account
```

The agent will pull your account list, existing dimensions, and tag keys from the API and fill in the templates. You then add the business context the API can't know — which team owns which account, what dimensions you want to build, how shared costs should be split.

### Manual path

No MCP required. Open the files in `my-org/`, fill in the templates, and start asking your agent to write dimensions. Even partial context (just your account list, or just your tag conventions) significantly improves output quality.

## For Claude Code Users

If you want the skill available in every workspace without cloning each time, add it as a custom skill:

```bash
# From inside the costformation-brain directory
claude skill install .
```

Or reference it in your project's `CLAUDE.md`:

```markdown
## CostFormation
When working on CostFormation YAML, consult the corpus in `costformation-brain/`.
Always read `costformation-brain/SKILL.md` first.
```

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
| Claude Code Skills | https://docs.cloudzero.com/docs/ai-skills |
