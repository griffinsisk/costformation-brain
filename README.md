# CloudZero CostFormation Brain

An AI knowledge corpus that makes any coding agent an expert at writing CloudZero CostFormation YAML. Drop it into your project and your AI assistant writes correct, performant definitions on the first try.

Works with Claude Code, Cursor, Copilot, Codex, Windsurf — any IDE or CLI with an AI assistant.

## Quick Start

### 1. Clone the brain into your project

```bash
cd your-project
git clone https://github.com/griffinsisk/costformation-brain.git
python3 costformation-brain/workspace/init.py .
```

The initializer creates customer-specific `my-org/`, `context/`, and
`.costformation/` state beside the clone. Customer data never lives inside the
`costformation-brain` Git repository.

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
  --data-binary @costformation.proposed.cz.yaml \
  https://api.cloudzero.com/v1/cost-formation/definitions
```

## Build Harness

The agent works from a two-file pair in your workspace: `costformation.cz.yaml`
is the latest baseline downloaded from CloudZero and is never edited, and
`costformation.proposed.cz.yaml` is the complete proposed definition the agent
builds and updates.

At the start of a session, the agent inventories whatever MCP servers you have
connected and classifies them by capability (cloud inventory, metrics,
observability, business context, and so on) — there is no required vendor list.
Only read-only capabilities are used automatically; anything write-capable or
unclear requires your explicit approval per action.

Evidence gathered from these sources is distilled into small local records with
provenance under your customer workspace — never raw transcripts or full tool
responses, and never inside this repository.

Before handoff, the agent validates the workspace with
`python3 costformation-brain/validator/workspace_check.py .` and fixes all
errors. The agent never publishes: you review the proposal and publish it
yourself through the CloudZero VS Code Toolkit.

See `profiles/customer.md` for the full workflow.

## New to CloudZero? Use the Onboarding Journey

If your costformation file is nearly empty, the agent offers a guided, resumable
journey: it inventories the signals in your billing data (tags, account names,
resource names, K8s labels), proposes a starter set of dimensions with evidence,
maps which spend each dimension can't allocate, and walks you through splitting
shared costs — by simple rules, business metrics, or usage telemetry (it
generates the collector script and validates your payloads before you send).
The journey ends, optionally, at unit cost.

Say `onboard` or `suggest dimensions` to start; `continue onboarding` to resume.
Progress persists in `my-org/onboarding-state.yaml`, so multi-day steps (like
waiting for telemetry to land) pick up where you left off.

## How It Works

The instruction file you copied in step 3 forces the agent to read `SKILL.md` before writing any CostFormation YAML. That file contains non-negotiable rules (source prefixes, performance constraints, allocation design) and a routing table that points to 9 corpus files covering syntax, conditions and transforms, telemetry, allocation design, and real-world examples.

The `examples/` directory contains 20 structured CostFormation patterns — from basic account mappings to advanced allocation chains — each with metadata that helps the agent select the right starting point. The agent checks `examples/index.yaml` before writing any dimension from scratch.

The workspace-root `my-org/` directory stores your org-specific context. It is
outside the cloned repository, auto-populated from your CostFormation file and
the CloudZero MCP, and refreshed whenever you pull a new CostFormation version.

Without the instruction file, agents confidently generate wrong CostFormation syntax from general knowledge. The output looks plausible but uses incorrect structure. The brain fixes this.

## Validator and Eval

The repo includes a CostFormation linter and eval framework. Requires `ruamel.yaml` (`pip install ruamel.yaml`).

```bash
# Lint CostFormation files (11 error rules, 5 warning rules)
python3 validator/lint.py costformation.cz.yaml
python3 validator/lint.py examples/patterns/*.yaml

# Validate the complete proposal against its recorded baseline
python3 costformation-brain/validator/workspace_check.py .

# Validate distilled evidence and optional MCP capability manifests
python3 validator/evidence_check.py evidence.yaml
python3 validator/capability_check.py .costformation/capabilities.yaml

# Run capability-classification golden cases
python3 evals/harness_run.py

# Integrity checks (index consistency, anonymization scan)
python3 validator/lint.py --check-integrity

# Run eval cases against golden outputs
python3 evals/run.py --validate-golden
python3 evals/run.py --assert-golden
python3 evals/run.py --list

# Run tests (requires pytest)
python3 -m pytest tests/ -v

# Validate telemetry payloads before sending
python3 validator/telemetry_check.py payload.json \
  --costformation costformation.cz.yaml --target-dimension SpendCategory
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
