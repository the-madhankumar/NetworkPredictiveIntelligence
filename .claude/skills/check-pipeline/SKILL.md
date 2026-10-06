---
name: check-pipeline
description: Check pipeline status, recent execution health, rejected rows, and staleness.
disable-model-invocation: true
---

# Check Pipeline

Inspect the available pipeline status endpoint and recent pipeline outputs.

Check:

- latest pipeline execution
- success or failure status
- rejected rows
- output availability
- output freshness
- obvious pipeline errors

Use the existing backend/API implementation rather than inventing a new status source.

Return:

## STATUS

PASS, WARN, or FAIL

## LAST RUN

Report the most recent known execution.

## REJECTED ROWS

Report rejected-row information.

## STALENESS

State whether the analytics output appears current.

## EVIDENCE

List the actual evidence used.

## NEXT CHECKS

List human follow-up actions.