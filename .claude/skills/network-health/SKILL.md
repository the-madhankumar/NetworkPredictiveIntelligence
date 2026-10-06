---
name: network-health
description: Check the network analytics grain and report whether hourly_grid_summary is valid.
disable-model-invocation: true
---

# Network Health

Run the repository's grain-quality checks for `hourly_grid_summary`.

The canonical analytics grain is exactly one record per:

- grid_id
- timestamp

Check for duplicate `(grid_id, timestamp)` combinations.

Also check:

- missing grid_id
- missing timestamp
- unexpected null activity values
- stale analytics output when pipeline status is available

Run the appropriate existing test or validation command.

Return:

## STATUS

PASS or FAIL

## GRAIN CHECK

Report duplicate count.

## DATA QUALITY

Report important null or invalid-value findings.

## PIPELINE STATUS

Report the latest pipeline status if available.

## NEXT CHECKS

List only the checks a human should perform next.