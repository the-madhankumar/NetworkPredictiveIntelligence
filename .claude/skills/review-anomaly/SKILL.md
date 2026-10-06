---
name: review-anomaly
description: Compare rule alerts, classifier output, and anomaly scores for a network grid.
disable-model-invocation: true
---

# Review Anomaly

Input:

- grid_id

Compare the available evidence from:

1. rule-based alert
2. classifier output
3. anomaly score
4. relevant ML features
5. current activity
6. baseline
7. pipeline status

Do not automatically treat disagreement as an error.

Identify:

- agreement
- disagreement
- missing evidence
- stale data
- possible feature or pipeline issues

Return:

## RULE ALERT

State the rule result.

## CLASSIFIER

State the classifier result.

## ANOMALY SCORE

State the anomaly evidence.

## AGREEMENT

Explain where the signals agree.

## DISAGREEMENT

Explain where they disagree.

## NEXT CHECKS

Give the most useful human checks.