---
name: pipeline-troubleshooting
description: Diagnose Spark, Airflow, data-quality, partitioning, and analytics pipeline failures.
---

# Pipeline Troubleshooting

Investigate pipeline failures systematically.

Check:

1. input availability
2. schema
3. row counts
4. nulls
5. rejected rows
6. partition structure
7. Spark transformation errors
8. output row counts
9. hourly grain
10. Airflow task status
11. analytics freshness

Canonical analytics grain:

`grid_id + timestamp`

Check for duplicate records at this grain.

Do not silently repair bad raw data.

Raw data is immutable.

Separate:

- raw data problems
- transformation problems
- aggregation problems
- orchestration problems
- API problems

Return:

## FAILURE

What failed.

## EVIDENCE

Concrete logs, records, or test results.

## ROOT CAUSE

Only state a root cause when evidence supports it.

## IMPACT

Explain what downstream component is affected.

## NEXT CHECKS

Give the next diagnostic steps.