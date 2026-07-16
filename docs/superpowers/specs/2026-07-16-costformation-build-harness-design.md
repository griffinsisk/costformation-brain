# CloudZero CostFormation Build Harness — Design Spec

**Date:** 2026-07-16
**Status:** Approved design, pending implementation plan

## Summary

Evolve `costformation-brain` from a knowledge corpus into a profile-aware build
harness that turns customer evidence into a complete, validated CostFormation
proposal. The harness has a customer-safe public core and a private SE overlay.
Both profiles share the same CostFormation rules, evidence model, validation,
and two-file build lifecycle. The SE profile adds CloudZero-internal context
gathering from Salesforce, Granola, and Sybill.

The harness stops at a validated build artifact. A human reviews and publishes
through the CloudZero VS Code Toolkit.

## Product Framing

> A profile-aware build harness that gathers evidence from available systems,
> converts it into validated CloudZero CostFormation, and keeps humans in
> control of publishing.

The build-system mapping is:

| Build concept | CostFormation equivalent |
|---|---|
| Source | Latest downloaded `costformation.cz.yaml` |
| Dependencies | Corpus, customer documents, and MCP evidence |
| Build profile | Customer or SE |
| Discovery | Connected MCP capability inventory |
| Intermediate state | Distilled evidence and confirmed decisions |
| Build artifact | `costformation.proposed.cz.yaml` |
| Compiler | Agent following routed CostFormation rules |
| Static analysis | CostFormation validator |
| Tests | Eval cases and integrity checks |
| Review | Baseline-to-proposal diff |
| Deployment | Explicit publish through VS Code Toolkit |

## Goals

1. Give SEs a repeatable one-command way to initialize a POV workspace in the
   Google Drive Accounts hierarchy.
2. Keep the public customer distribution free of CloudZero-internal connector
   names, workflows, and assumptions.
3. Let both profiles gather evidence from whatever readable MCPs are available
   without hard-coding a vendor catalog.
4. Distill meeting and system evidence into source-linked facts without storing
   raw transcripts or full MCP responses.
5. Produce exactly one complete proposed CostFormation definition beside an
   untouched latest-downloaded baseline.
6. Preserve the existing corpus routing, performance rules, validator, evals,
   and VS Code Toolkit publishing workflow.
7. Prevent customer artifacts and evidence from entering either Git repository.

## Non-Goals

- Publishing CostFormation to CloudZero.
- Replacing the CloudZero VS Code Toolkit.
- Copying raw Granola or Sybill transcripts into a POV workspace.
- Maintaining an exhaustive list of supported MCP vendors.
- Automatically invoking write-capable third-party tools.
- Automatically promoting customer facts into shared documentation or a
  cross-customer knowledge graph.
- Introducing Graphiti in the first implementation. A reviewed evidence export
  can feed a graph later without changing the build contract.

## Chosen Architecture

### Public core: `costformation-brain`

The existing repository remains customer-safe and owns:

- CostFormation corpus, routing, examples, onboarding, validator, and evals.
- CloudZero MCP querying requirements.
- Generic optional-MCP capability discovery and query planning.
- Read-only-by-default external connector policy.
- Normalized evidence, authority, freshness, and contradiction rules.
- The two-file baseline/proposal workflow.
- Customer-profile instructions.

Customer-facing runtime instructions, setup documentation, profiles, and
generated artifacts in the public core must not mention Salesforce, Granola,
Sybill, CloudZero sales processes, or internal data sources. Historical design
specifications may describe the boundary, but they are not routed or copied by
customer setup. An integrity test enforces the runtime and distribution
boundary.

### Private overlay: `costformation-se`

A separate private repository is installed once on an SE workstation and owns:

- The `cz-pov` bootstrap and health-check CLI.
- SE-profile instructions and source-authority extensions.
- Salesforce account and opportunity resolution strategy.
- Granola customer-statement and decision gathering strategy.
- Sybill objection, next-step, and deal-interpretation gathering strategy.
- In-memory distillation and contradiction detection.
- POV evidence-coverage reporting.
- An anonymized learning-candidate exporter that always requires review.
- Public-core compatibility metadata.

The private repository contains no customer data. It references schemas from a
compatible public-core version instead of copying them.

### Local customer workspace

The customer workspace is the only location that may contain customer-specific
documents, evidence, decisions, or CostFormation definitions. It is normally a
folder under the CloudZero Google Drive `Shared drives/Accounts` hierarchy.

```text
Customer Name/
├── costformation-brain/             # public core clone
├── context/
│   ├── provided/                    # customer plans, diagrams, CSVs
│   ├── evidence/                    # distilled, source-linked evidence
│   ├── decisions/                   # confirmed POV decisions
│   └── index.yaml                   # compact retrieval summary
├── .costformation/
│   ├── profile.yaml                 # customer or se
│   ├── capabilities.yaml            # detected readable capabilities
│   ├── gathering-state.yaml         # freshness and workflow position
│   └── privacy-policy.yaml          # persisted safety policy
├── costformation.cz.yaml            # untouched latest download
├── costformation.proposed.cz.yaml   # one complete proposed definition
├── CLAUDE.md / AGENTS.md            # generated profile-aware routing
└── .gitignore
```

`cz-pov init "Customer Name"` creates this structure from the Accounts folder,
clones or updates the public core, and generates the SE-aware root instructions.
It does not clone the private overlay into every customer workspace.

Customer artifacts remain outside `costformation-brain/`. The bootstrap checks
repository boundaries and writes ignore rules as defense in depth. It must work
correctly in Google Drive paths containing spaces.

## Profile Composition

The root agent instruction file routes to the public core first. In an SE
workspace, generated instructions add private overlay routing without altering
files inside the public clone. The composition order is:

1. Public non-negotiable CostFormation rules.
2. Public customer-safe evidence and MCP policy.
3. SE-only source discovery and authority extensions, when profile is `se`.
4. Local customer context and state.

The customer profile works by cloning `costformation-brain` as it does today.
It never needs the private CLI or private repository.

## Generic MCP Capability Model

The public core models capabilities rather than vendors. Initial capability
categories are:

- `cloud_inventory`
- `resource_metadata`
- `metrics`
- `usage_volume`
- `observability`
- `business_context`
- `meeting_context`
- `crm`
- `documentation`

At session initialization, the agent inventories connected MCP servers and
their tool descriptions. Each readable tool is mapped to zero or more
capabilities and recorded locally. Unknown servers are usable when their tool
contracts map unambiguously to a supported capability.

```yaml
capabilities:
  - server: example-observability
    categories: [observability, metrics, usage_volume]
    access: read-only
    status: available
```

Tool classification is conservative:

- Read-only tools may be selected automatically when relevant.
- Write-capable tools are excluded from autonomous plans.
- Mixed or ambiguous tools are treated as write-capable.
- A write invocation requires explicit approval for that specific action.
- Credentials and authentication tokens are never written to capability files.

This permits optional AWS, Azure, GCP, Datadog, and other MCPs without adding a
separate integration module for each vendor.

## Source Authority

Sources answer different questions; they are not interchangeable.

| Source | Authoritative for |
|---|---|
| CostFormation baseline | Current local implementation and naming conventions |
| CloudZero MCP | What CloudZero currently sees: accounts, dimensions, tags, resources, spend, telemetry |
| Customer documents | Customer-authored architecture, plans, mappings, and constraints |
| Cloud/observability MCPs | Upstream resource metadata, metrics, usage, and operational signals |
| Salesforce (SE only) | Account, opportunity, stage, ownership, stakeholders, and POV scope |
| Granola (SE only) | Customer statements, discussions, and meeting decisions |
| Sybill (SE only) | Objections, next steps, and sales/deal interpretation |
| Human confirmation | Business meaning, ownership, goals, and accepted decisions |
| Shared corpus | Accepted CostFormation syntax, design, and performance rules |

When CloudZero differs from an upstream system, CloudZero governs what is
currently available to CostFormation. The upstream fact remains useful as
evidence of intended or not-yet-ingested state.

## Evidence Model

Granola and Sybill results are processed in memory. The workspace persists only
distilled claims with enough provenance to reopen the source.

Required evidence fields are:

```yaml
evidence_id: ev_01...
pov_id: pov_01...
source_system: granola
source_record_id: meeting_01...
source_url: https://...
captured_at: 2026-07-16T14:30:00Z
speaker: Customer Name
evidence_type: customer_statement
subject: environment_mapping
statement: Production is represented by prod and prd.
status: customer-confirmed
confidence: confirmed
customer_scope: customer-only
promotion_status: unreviewed
```

Supported evidence statuses are:

- `observed`: directly returned from a system.
- `customer-confirmed`: explicitly stated or approved by the customer.
- `inferred`: reasoned from multiple signals and not confirmed.
- `conflicting`: credible sources disagree.
- `stale`: the source or baseline changed after capture.

An inference never silently becomes a confirmed fact. Raw transcripts, full
tool responses, credentials, and unrelated meeting content are prohibited.

## Build Lifecycle

### 1. Initialize and inventory

The harness creates or reconciles the workspace, locates the CostFormation
baseline, indexes `context/provided/`, inventories MCP capabilities, and checks
profile compatibility and privacy policy.

### 2. Resolve POV scope

The customer profile uses local context and direct confirmation. The SE profile
first resolves the Salesforce account, opportunity, customer domain,
participants, owner, and date range. Salesforce IDs are the preferred join keys;
fuzzy company-name matching alone is insufficient.

### 3. Gather business context

The customer profile uses customer documents, direct confirmation, CloudZero,
and any optional readable MCPs. The SE profile additionally queries Granola and
Sybill within the resolved POV scope. Independent queries run concurrently.

### 4. Gather technical signals

The agent decomposes the requested CostFormation concept into signal questions.
For an Environment dimension, it checks tags, account names, resource names,
Kubernetes data, existing dimensions, spend coverage, customer architecture,
and relevant upstream metadata or observability signals.

CloudZero remains mandatory when connected and is queried first for dimension
creation or modification, consistent with the existing corpus contract.

### 5. Reconcile

The harness normalizes results, deduplicates claims, checks freshness, exposes
contradictions, and distinguishes observation from inference. It asks the human
only for business meaning or choices that available data cannot answer.

### 6. Build and validate

The agent follows the existing corpus routing and example selection rules,
creates the complete proposed definition, runs the validator, fixes all errors,
and reports remaining warnings plus an evidence-coverage and diff summary.

### 7. Human publish and record outcome

The user reviews and publishes through the VS Code Toolkit. After the latest
definition is downloaded again, the new baseline becomes the source for the
next proposal. Accepted or rejected decisions are recorded locally. The SE may
explicitly export a reviewed, anonymized learning candidate; no automatic
cross-customer promotion occurs.

## Two-File CostFormation Contract

The prior timestamped-backup and per-change-folder workflow is replaced.

### Baseline

`costformation.cz.yaml` is the immutable local representation of the latest
definition downloaded through VS Code Toolkit. The harness never edits it.

### Proposal

`costformation.proposed.cz.yaml` is the only generated CostFormation working
file. It contains the complete proposed definition and is always validated as a
whole.

Before writing a proposal, the harness compares the two files:

- If they match, the proposal may be regenerated from the baseline.
- If they differ, the user chooses to retain, replace, or rebase the proposal.
- If the baseline changed after proposal creation, validation and handoff stop
  until the proposal is rebased or deliberately replaced.
- The harness never creates timestamped backups, dimension snippet files, or
  per-change comment files.
- Review context is delivered as an on-demand diff summary and compact local
  decision record.

Implementation must update `AGENTS.md`, `CLAUDE.md`, `SKILL.md`, and equivalent
IDE instruction files so they no longer require backups and change folders.

## Safety Invariants

1. Never edit `costformation.cz.yaml`.
2. Never publish to CloudZero.
3. Never persist raw meeting transcripts or complete MCP responses.
4. Never invoke an external write operation without explicit approval.
5. Never write customer-specific artifacts inside either repository.
6. Never promote a customer fact into shared knowledge automatically.

## Failure Handling

| Failure | Required behavior |
|---|---|
| MCP unavailable | Continue with other sources and report the coverage gap |
| Authentication expired | Name the connector and provide reconnection guidance |
| Unknown MCP | Classify conservatively; omit ambiguous and write-capable tools |
| Conflicting evidence | Preserve both claims and request confirmation |
| Stale evidence | Mark stale and re-query before relying on it |
| CloudZero/upstream disagreement | Use CloudZero for current cost visibility; retain upstream evidence |
| Existing divergent proposal | Require retain, replace, or rebase choice |
| Refreshed baseline | Block handoff until proposal is reconciled |
| Validator error | Block presentation as publish-ready |
| Sensitive write into repo | Block and redirect to local workspace |
| Private/public version mismatch | Stop SE initialization and provide compatible upgrade guidance |

## Testing Strategy

### Public core

- Capability classification from representative MCP tool descriptions.
- Read-only, mixed, ambiguous, and write-capable tool filtering.
- Query routing by capability rather than vendor name.
- Missing and unavailable connectors.
- Evidence normalization and provenance requirements.
- Contradiction and freshness handling.
- Baseline immutability and full-proposal validation.
- Proposal drift after a new baseline download.
- Integrity scan excluding internal connector names from customer-facing
  runtime, setup, profile, and generated-distribution files.
- Existing CostFormation validator and golden-output regression coverage.

### Private overlay

- Salesforce account and opportunity resolution.
- Granola and Sybill result distillation.
- Removal of raw transcript and unrelated content.
- SE profile composition without modifying the public clone.
- Public-core compatibility enforcement.
- Anonymized learning-candidate generation with review gate.
- Bootstrap behavior in Google Drive paths containing spaces.
- Assurance that customer artifacts never enter either Git repository.

### End-to-end dry runs

Run one customer-profile and one SE-profile scenario. Each must end with:

- an untouched `costformation.cz.yaml`;
- one complete, validator-clean `costformation.proposed.cz.yaml`;
- distilled evidence with provenance;
- no raw transcript or full MCP response on disk;
- no automated external mutation or CloudZero publish; and
- no customer artifacts in either Git worktree.

## Delivery Sequence

1. Implement the two-file contract and workspace safety checks in the public
   core.
2. Add the public evidence schema, authority rules, capability model, discovery
   workflow, and customer-profile evals.
3. Create the private overlay and `cz-pov` bootstrap with compatibility checks.
4. Add Salesforce resolution and Granola/Sybill distillation workflows.
5. Run customer and SE end-to-end dry runs before treating the harness as ready.
6. Evaluate cross-POV knowledge promotion and Graphiti only after evidence
   capture and review behavior are calibrated on real POVs.

## Success Criteria

- An SE can create a correctly structured POV workspace with one command.
- A customer can use the public core without seeing or requiring internal tools.
- The harness uses relevant connected MCPs without assuming specific vendors.
- No external mutation occurs without explicit approval.
- No raw meeting content or customer artifact enters Git.
- Every persisted claim has provenance and an explicit epistemic status.
- The baseline remains untouched and only one complete proposal is generated.
- The proposal passes the CostFormation validator before handoff.
- Publishing remains a deliberate human action through VS Code Toolkit.
