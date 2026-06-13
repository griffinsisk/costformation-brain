<!-- APPEND-ONLY: Never delete or replace content in this file. Only add new content below existing sections. This file preserves business context across sessions. -->

# My Organization — Business Context

This file is append-only. The agent adds business context from conversations below. Existing content must never be removed or overwritten — only appended to.

You can also edit this file directly.

## Organization Structure

## Cost Views & Goals

## Shared Resources

## Constraints & Preferences

## Onboarding Journey — pending calibration (added 2026-06-12)

The onboarding journey (onboarding/journey.md, phases 1-5, telemetry_check.py,
collector template) shipped on branch onboarding-journey. Per the
calibrate-before-depending rule, do NOT consider it customer-ready until:

- [ ] Calibrate telemetry_check.py against at least one REAL customer payload
- [ ] MCP dry-run: phases 1-3 against a real customer costformation file from
      reference/customer-examples/, across two sessions (verify resume)
- [ ] Cross-IDE dry-run: phases 1-2 in a non-Claude agent (e.g. Cursor);
      tighten phase docs where drift shows up
- [ ] Abandonment path: seed my-org/onboarding-state.yaml with an overdue
      verify-after, start a fresh session, confirm the wait check fires
      with no onboarding phrase used
