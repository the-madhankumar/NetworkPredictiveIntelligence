---
name: explain-grid
description: Explain a selected network grid using activity, baseline, features, anomaly score, and location evidence.
---

# Explain Grid

Input:

- grid_id

Gather available evidence for that grid:

- current activity
- baseline activity
- activity direction
- anomaly score
- anomaly or rule alerts
- ML risk score
- relevant feature values
- location/geography
- pipeline freshness

The canonical grid is a geographic cell.

Do not describe a grid as a tower.

Activity values are activity measures.

Do not describe activity values as:

- counts
- MB
- confirmed congestion

If evidence is missing, explicitly state that the evidence is insufficient.

Return exactly:

## SEVERITY

State severity only if sufficient evidence exists.

## EVIDENCE

List the observed values and their sources.

## INTERPRETATION

Explain what the evidence supports.

Do not claim confirmed congestion merely because activity is high.

## NEXT CHECKS

List the next checks a NOC operator should perform.