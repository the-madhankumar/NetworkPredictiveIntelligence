# Context and Cost Optimization Guideline

## Purpose

The NOC assistant should provide sufficient evidence for a reliable decision without unnecessarily sending large raw datasets to the model.

## Evidence Selection

Prefer curated evidence:

* current activity
* historical baseline
* anomaly score
* risk score
* top contributing features
* relevant alerts
* pipeline status
* geographic information
* neighbouring-grid evidence when required

Avoid sending complete historical datasets when a curated analytical representation answers the question.

## Model Selection

Use a fast/efficient model for:

* simple status checks
* pipeline summaries
* API responses
* deterministic formatting
* short explanations

Use a stronger reasoning model for:

* conflicting anomaly evidence
* multi-agent investigation
* complex root-cause analysis
* ambiguous NOC incidents
* engineering review

## Context Strategy

Use the smallest evidence set that can support the decision.

Prefer:

`curated evidence -> reasoning`

over:

`raw dataset -> reasoning`

## Retrieval Strategy

Retrieve additional evidence only when the existing evidence is insufficient.

Do not preload all available network data.

## Quality Rule

Reducing context is acceptable only when important evidence is preserved.

A smaller context that removes the evidence required for a correct decision is not an optimization.

## Evaluation

Compare:

* context size
* estimated token usage
* latency
* answer quality
* missing evidence
* incorrect conclusions

The final strategy should be based on measured results rather than assumptions.
