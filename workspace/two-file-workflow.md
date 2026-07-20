# Two-File CostFormation Workflow

The workspace has one immutable baseline and one complete proposal:

- `costformation.cz.yaml` — the latest definition downloaded through the
  CloudZero VS Code Toolkit. Never edit this file.
- `costformation.proposed.cz.yaml` — the only CostFormation working file. It
  contains the complete proposed definition, not a dimension snippet.

Before building:

1. Confirm `costformation.cz.yaml` is the latest downloaded definition.
2. If no proposal exists, copy the complete baseline to
   `costformation.proposed.cz.yaml` and edit only the proposal.
3. If a proposal exists and differs from the baseline, show a concise diff and
   ask whether to retain, replace, or rebase it. Never overwrite it silently.
4. Record the baseline SHA-256 used by the proposal in
   `.costformation/gathering-state.yaml`.

Before handoff:

1. Verify the current baseline SHA-256 matches the proposal's recorded
   `baseline-sha256`.
2. Run `python3 costformation-brain/validator/workspace_check.py .`.
3. Fix every ERROR before presenting the proposal as publish-ready.
4. Summarize the baseline-to-proposal diff and any remaining WARNINGs.

Publishing is always a deliberate human action through the CloudZero VS Code
Toolkit. The harness never edits the baseline and never publishes.
