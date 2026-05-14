# 2026-05-14 Session Handoff

## Current State

Phase 1 and Phase 2 are complete.

- Phase 1: 20 structured examples and corpus enrichment.
- Phase 2: validator CLI and eval framework.
- Validator was calibrated against 6 real customer example files in `reference/customer-examples/`.
- Agent workflow docs now require validation before presenting generated or modified CostFormation YAML.

Latest reviewed workflow commit:

- `d3c4b3b Wire validator into agent workflow: validate before presenting`

## Validator Calibration Results

Customer examples produced calibrated diagnostics:

- Files checked: 6
- Errors: 2173
- Warnings: 326

Errors:

- `unquoted-account-id`: 2170
- `defaultvalue-allocation-input`: 3

Warnings:

- `defaultvalue-hidden-performance`: 61
- `defaultvalue-no-intent`: 142
- `visible-no-child`: 117
- `broad-spendtoallocate`: 6

Important interpretation:

- The remaining error rules were reviewed as true positives.
- Warnings are useful flags, not customer-output blockers.
- Do not make `--warnings-as-errors` part of normal customer generation.

## Agent Workflow Policy

The current intended policy is:

1. Agents read the CostFormation corpus before generating YAML.
2. After generating or modifying CostFormation YAML, agents run:

   ```bash
   python3 costformation-brain/validator/lint.py <file>
   ```

3. Agents fix all `ERROR`s before showing YAML to the customer.
4. Agents briefly summarize any remaining `WARNING`s.
5. Warnings do not block customer-facing work.
6. `--warnings-as-errors` is reserved for corpus/examples/eval maintenance.

This policy is now documented in:

- `SKILL.md`
- `CLAUDE.md`
- `AGENTS.md`
- `.cursorrules`
- `.github/copilot-instructions.md`

## Verification From Final Review

Fresh verification completed after workflow wiring:

```bash
python3 validator/lint.py examples/patterns/*.yaml
# OK: 20 files, 0 errors, 2 warnings

python3 validator/lint.py --check-integrity
# OK: 1 file, 0 errors, 0 warnings

python3 evals/run.py --validate-golden
# 9/9 passed

python3 evals/run.py --assert-golden
# 9/9 cases passed, 28 assertions checked, 0 failed, 0 skipped

python3 -m pytest tests -q
# 50 passed
```

Working tree was clean after the review.

## Recommendations To Preserve

Recommended next sequence:

1. Add CI or pre-publish automation for validator and eval checks.
   - Run `python3 validator/lint.py examples/patterns/*.yaml`.
   - Run `python3 validator/lint.py --check-integrity`.
   - Run `python3 evals/run.py --validate-golden`.
   - Run `python3 evals/run.py --assert-golden`.
   - Run `python3 -m pytest tests -q`.

2. Add a generated-output repair loop test.
   - Start with a known-bad CostFormation fixture.
   - Verify validator catches it.
   - Verify the expected repaired output passes.
   - Keep this deterministic before adding an LLM-in-the-loop runner.

3. Add LLM-in-the-loop evals only after deterministic checks stay stable.
   - Use the existing eval case format.
   - Treat assertions plus validator diagnostics as the contract.
   - Golden YAML remains an example, not an exact-output requirement.

4. Delay domain sub-skills until there is evidence that corpus routing is hurting agent output.
   - Domain sub-skills may be useful for `aws-account-mapping`, `k8s-allocation`, `shared-cost`, and debugging.
   - Do not split the corpus just because it is larger.
   - Let eval failures or repeated agent misses identify the split points.

5. Consider RAGAS later, but not as the next step.
   - The current highest-value quality signal is deterministic CostFormation validity.
   - RAGAS may help evaluate retrieval quality or corpus answer faithfulness later.
   - It should not replace the validator or structured assertions.

## Watch Items

- The validator command path assumes the README clone layout: `costformation-brain/validator/lint.py`.
- Integrity output currently reports `OK: 1 file` for `--check-integrity`, which is technically passing but not very descriptive.
- Real customer example files intentionally retain legacy issues; do not auto-fix them unless that becomes an explicit task.
- Continue treating customer example diagnostics as calibration data before adding stricter rules.
