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
git clone https://github.com/griffinsisk/costformation-brain.git

# Your workspace should look like this:
# my-costformation/
#   costformation.cz.yaml        ← your dimension file
#   costformation-brain/          ← this repo
#     CLAUDE.md
#     SKILL.md
#     concepts.md
#     examples.md
#     my-org/
#     ...
```

Or download and unzip — no git required.

### 3. Copy the agent instructions to your workspace root

This is the critical step. AI agents don't reliably read local files before acting — they'll generate CostFormation from memory and get it wrong. The instruction files force them to consult the brain first.

**Claude Code:**
```bash
cp costformation-brain/CLAUDE.md ./CLAUDE.md
```

**Cursor:**
```bash
cp costformation-brain/.cursorrules ./.cursorrules
```

**GitHub Copilot:**
```bash
mkdir -p .github && cp costformation-brain/.github/copilot-instructions.md .github/
```

**Codex / other agents:**
```bash
cp costformation-brain/AGENTS.md ./AGENTS.md
```

### 4. Start editing

Open `my-costformation/` in your IDE or CLI. The agent instructions load automatically and force the AI to read the brain before writing any YAML.

```bash
cd my-costformation
claude
# "Add a Team dimension that maps K8s labels to engineering teams"
```

The agent will read SKILL.md, check your my-org/ context, consult performance-rules.md, and then generate correct CostFormation YAML.

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

## Why the Copy Step Matters

AI agents (Claude, Cursor, Copilot, Codex) will confidently generate CostFormation YAML from general knowledge. The output looks plausible but uses wrong syntax — flat `Source/Contains` keys instead of proper CFDL structure with `Conditions`, `Type: Group`, plural `Sources`, `CoalesceSources`, transforms, etc.

The instruction files (`CLAUDE.md`, `.cursorrules`, `copilot-instructions.md`, `AGENTS.md`) are loaded automatically by each IDE before the agent responds. They force the agent to read the brain's corpus before writing anything. Without this step, the brain sits in the directory unused.

## Included Instruction Files

| File | IDE/CLI | Auto-loaded? |
|---|---|---|
| `CLAUDE.md` | Claude Code | Yes, when in workspace root |
| `.cursorrules` | Cursor | Yes, when in workspace root |
| `.github/copilot-instructions.md` | GitHub Copilot | Yes, when in workspace root |
| `AGENTS.md` | Codex, Gemini CLI, others | Varies by tool |
| `SKILL.md` | Any agent (manual read) | Only if instructed |

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

## Sources

This corpus is built from real CloudZero engineering knowledge and customer implementations:

| What | Source | Used In |
|---|---|---|
| Performance rules, allocation design, DefaultValue guidance, expansion factor formula | CloudZero Engineering — *CostFormation Best Practices* (Confluence, Matt Yellen, Aug 2025) | `performance-rules.md`, `allocation-design.md` |
| 10 worked examples (anonymized) | 12 real customer CostFormation files from the Accounts shared drive | `examples.md` |
| Complete dimension reference (CostFormation syntax, API refs, telemetry filter keys) | *CZ Dimension Reference* spreadsheet | `sources.md`, `telemetry.md` |
| Non-negotiable rules, condition/transform syntax | CFDL language reference + internal engineering tribal knowledge | `SKILL.md`, `conditions.md`, `transforms.md` |
