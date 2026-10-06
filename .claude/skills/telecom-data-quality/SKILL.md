---
name: telecom-data-quality
description: Validate telecom activity data, grain, schema, leakage, nulls, and analytical correctness.
---

# Telecom Data Quality

Validate data using the project's canonical definitions.

Raw activity values are activity measures.

Do not describe them as counts or MB unless the source explicitly defines them that way.

The canonical analytics grain is:

`one grid per hourly timestamp`

Check:

- duplicate `(grid_id, timestamp)`
- missing grid_id
- missing timestamp
- invalid activity values
- unexpected nulls
- incorrect joins
- geography mapping
- current-period leakage
- baseline leakage
- feature leakage

Geography must join using:

`properties.cellId`

The baseline must exclude the current interval.

The AS_OF convention defines the current reporting window.

Raw data is immutable.

Return:

## STATUS

PASS or FAIL.

## GRAIN

Report duplicate findings.

## SCHEMA

Report schema problems.

## LEAKAGE

Report current-period or baseline leakage.

## GEOGRAPHY

Report geography join issues.

## NEXT CHECKS

List remediation steps.