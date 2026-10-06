---
name: network-anomaly-analysis
description: Analyze why a network grid is flagged, whether a pattern is unusual, or what an anomaly score means.
---

# Network Anomaly Analysis

Use this skill when investigating an anomalous or flagged grid.

Required evidence:

- current activity
- baseline activity
- activity direction
- anomaly score
- rule alerts
- ML risk score when available
- relevant feature values
- pipeline status/freshness

If the evidence is incomplete, explicitly say that severity cannot be determined reliably.

Never invent missing values.

Never equate high activity with confirmed congestion.

Activity is an activity measure, not a count and not MB.

A grid is a geographic cell, not a tower.

The canonical analytics grain is:

`grid_id + timestamp`

The baseline must exclude the current interval.

Use the project's AS_OF convention when determining the current reporting window.

Return:

## SEVERITY

Only when evidence supports it.

## EVIDENCE

Observed facts and source.

## INTERPRETATION

What the evidence means.

## NEXT CHECKS

Human-verifiable follow-up actions.

Do not fill gaps with assumptions.