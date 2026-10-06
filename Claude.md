# Network Operations & Predictive Intelligence

## 1. Project Purpose

This repository contains a Network Operations and Predictive Intelligence platform for analyzing telecom network activity, identifying unusual activity patterns, generating network risk scores, and exposing network intelligence through APIs and a React dashboard.

The system combines:

* Telecom activity data
* Spark-based data processing
* Airflow orchestration
* Machine learning
* FastAPI services
* React visualization
* Network anomaly and risk analysis
* Claude-based intelligence capabilities

The system supports NOC-style investigation and predictive analysis.

---

# 2. Repository Structure

```text
Project 2/
├── Dataset/
│   ├── analytics/
│   │   └── ML_LAYER/
│   │       ├── anomaly_detection/
│   │       ├── network_risk_scores/
│   │       └── risk_classifier/
│   ├── landing/
│   ├── processed/
│   │   └── activity/
│   ├── raw/
│   ├── reference/
│   └── SP2/
│
├── log/
│
├── Phase 1/
├── Phase 2/
├── Phase 3/
├── Phase 6/
├── Project Workflow/
│
└── src/
    ├── AirFlow/
    │   ├── dags/
    │   │   └── Phase3/
    │   │       ├── DE1/
    │   │       ├── DE2/
    │   │       ├── DE3/
    │   │       ├── DE4/
    │   │       ├── DE5/
    │   │       ├── DE7/
    │   │       └── DE8/
    │   └── data/
    │
    ├── Backend/
    │   ├── routes/
    │   └── service/
    │
    ├── Claude_Layer/
    │   ├── context/
    │   └── tools/
    │
    ├── Frontend/
    │   ├── public/
    │   └── src/
    │       ├── api/
    │       ├── assets/
    │       ├── components/
    │       │   ├── HotspotAndGrid/
    │       │   ├── NetworkGrid/
    │       │   ├── NetworkSummary/
    │       │   └── Predict/
    │       └── Pages/
    │           └── Dashboard/
    │
    └── ML Layer/
```

When locating functionality, inspect the existing implementation rather than creating duplicate modules.

---

# 3. System Architecture

The high-level data flow is:

```text
Raw Telecom Activity
        ↓
Landing / Validation
        ↓
Spark Processing
        ↓
Processed Activity
        ↓
Analytics / Feature Engineering
        ↓
ML Layer
        ↓
Risk Scores / Anomaly Detection
        ↓
FastAPI Backend
        ↓
React Frontend
        ↓
NOC / Network Intelligence
```

Airflow orchestrates the data pipeline and validation workflow.

FastAPI exposes existing network intelligence through backend routes.

The React application consumes the backend APIs for visualization and investigation.

Claude-based components must use existing APIs and services where possible instead of duplicating business logic.

---

# 4. Important Components

## Spark Pipeline

Location:

```text
src/AirFlow/
```

Responsible for:

* ingestion
* validation
* transformation
* aggregation
* feature preparation
* analytics generation

Spark transformations must preserve the intended hourly network grain.

---

## Airflow

Location:

```text
src/AirFlow/dags/Phase3/
```

Responsible for:

* pipeline orchestration
* validation
* quality checks
* task sequencing
* failure handling
* pipeline status

Do not move business logic unnecessarily from existing services into DAG definitions.

---

## Backend

Location:

```text
src/Backend/
```

Contains:

```text
routes/
service/
```

Routes expose API contracts.

Services contain reusable business logic.

When adding functionality, prefer:

```text
Route
  ↓
Service
  ↓
Existing data / model logic
```

Do not duplicate business calculations inside routes, Claude tools, or frontend code.

---

## ML Layer

Location:

```text
src/ML Layer/
```

Responsible for:

* feature generation
* anomaly detection
* risk classification
* network risk scoring
* model outputs

Model features must not contain future information.

---

## Frontend

Location:

```text
src/Frontend/
```

React components and pages consume FastAPI endpoints.

Follow existing component and API patterns rather than introducing a separate frontend architecture.

---

## Claude Layer

Location:

```text
src/Claude_Layer/
```

Claude-related functionality should remain separated from core business logic.

Claude should consume existing APIs/services rather than independently implementing:

* database queries
* risk calculations
* anomaly calculations
* network aggregation
* business rules

---

# 5. Canonical Data Grain

The canonical analytics grain is:

```text
one grid per hourly timestamp
```

The unique analytical key is:

```text
grid_id + timestamp
```

Every transformation, aggregation, feature-generation step, API response, and ML dataset must respect this grain unless a different grain is explicitly required and documented.

Always check for accidental duplicate:

```text
(grid_id, timestamp)
```

records.

Do not silently accept duplicated hourly grid records.

---

# 6. Geography Rule

The canonical geography mapping is:

```text
properties.cellId → grid_id
```

When joining network activity with the Milan grid GeoJSON, use:

```text
properties.cellId
```

Do not substitute:

* row number
* dataframe index
* unrelated IDs
* positional matching
* arbitrary geographic identifiers

unless the existing implementation explicitly defines them as equivalent.

---

# 7. Activity Definition

Network activity values represent **activity measures**.

They are not automatically:

* customer counts
* message counts
* MB
* bandwidth
* confirmed traffic volume

Do not change the meaning of the source data through terminology.

If the source explicitly defines a field differently, preserve that documented definition.

---

# 8. Congestion Rule

## NON-NEGOTIABLE

High activity does **not** mean confirmed congestion.

Do not make statements such as:

```text
High activity means the grid is congested.
```

Instead use language such as:

```text
The grid shows elevated activity.
```

or:

```text
The grid has a high activity/risk signal.
```

Confirmed congestion requires appropriate capacity or network-performance evidence that may not be present in this dataset.

Do not invent such evidence.

---

# 9. Baseline Rules

When comparing current activity against a baseline:

```text
current interval
        ↓
compare against
        ↓
historical baseline
```

The baseline must exclude the current interval.

Do not allow the current observation to leak into its own baseline.

When implementing future prediction:

```text
features available at t
        ↓
predict t+1
```

Do not use information from the target interval when generating features.

---

# 10. AS_OF Convention

`AS_OF` defines the current reporting window.

When implementing current-period analysis:

```text
AS_OF
  ↓
current reporting window
  ↓
current activity
  ↓
baseline comparison
```

Do not use future observations when determining the current state.

---

# 11. Machine Learning Rules

ML features must be generated only from information available at the feature timestamp.

Check for:

* future activity leakage
* future labels
* future aggregates
* current-period leakage
* baseline leakage
* target leakage

The target for future prediction must represent the future interval.

For example:

```text
t-2
t-1
 t
 ↓
features
 ↓
predict t+1
```

not:

```text
t+1 information
 ↓
features
 ↓
predict t+1
```

---

# 12. Terminology Rules

Use:

```text
grid
geographic cell
activity
activity measure
risk
risk score
anomaly
anomaly score
prediction
baseline
```

Avoid incorrectly using:

```text
tower
traffic count
MB
confirmed congestion
```

unless the underlying source explicitly supports that meaning.

A grid is a geographic cell, not a tower.

---

# 13. API Rules

Existing API contracts should remain backward compatible whenever possible.

Prefer additive API changes.

Before changing an endpoint:

1. Inspect the existing route.
2. Inspect the service implementation.
3. Check frontend consumers.
4. Check existing tests.
5. Identify the current response contract.
6. Make the smallest compatible change.
7. Add or update tests.

Do not rename or remove existing response fields without a clear reason and explicit approval.

---

# 14. Claude / AI Rules

Claude is an intelligence layer, not the source of truth.

When Claude needs network information:

```text
Claude
  ↓
existing API/tool
  ↓
actual data
  ↓
Claude interpretation
```

Never invent:

* grid values
* activity values
* risk scores
* anomaly scores
* timestamps
* geographic information
* pipeline status
* model predictions

If information is unavailable, explicitly state that the available evidence is insufficient.

Claude must distinguish:

```text
Observed fact
      ↓
Model output
      ↓
Interpretation
      ↓
Uncertainty
```

Do not present an interpretation as an observed fact.

---

# 15. Development Rules

Before modifying code:

1. Inspect the relevant existing implementation.
2. Understand the current data flow.
3. Reuse existing services and utilities.
4. Make the smallest necessary change.
5. Preserve existing behaviour.
6. Add or update tests.
7. Run relevant tests.
8. Review the final diff.

Do not create duplicate implementations when an existing service already provides the required functionality.

---

# 16. Testing Rules

Important tests should cover:

* hourly grain
* duplicate `(grid_id, timestamp)`
* missing grid IDs
* missing timestamps
* invalid activity values
* null values
* geographic joins
* feature leakage
* baseline leakage
* API contracts
* ML outputs
* anomaly/risk behaviour
* pipeline failures

When modifying Spark or ML code, check grain and leakage.

When modifying API code, check API contract compatibility.

When modifying geography logic, verify:

```text
properties.cellId → grid_id
```

---

# 17. Data Safety

Raw data is immutable.

Do not:

* delete raw data
* overwrite raw data
* silently repair raw records
* expose secrets
* commit API keys
* commit credentials
* modify production-like data without explicit approval

Prefer creating corrected outputs in processed/rejected areas rather than changing raw inputs.

---

# 18. Security

Never read or expose:

```text
.env
.env.*
secrets/
credentials/
API keys
tokens
passwords
private credentials
```

Do not place secrets in source code.

Use environment variables for credentials.

Do not commit secrets to Git.

---

# 19. File Modification Policy

For normal development:

```text
Read → Understand → Plan → Edit → Test → Review
```

Do not make broad repository-wide changes without justification.

Avoid unnecessary:

* dependency changes
* architecture changes
* renaming
* refactoring
* migrations
* configuration changes

Prefer minimal changes that satisfy the requirement.

---

# 20. Before Any Significant Change

For changes affecting:

* Spark processing
* Airflow
* ML features
* model outputs
* API contracts
* database schemas
* pipeline configuration

first explain:

```text
What will change
Why it is required
Which files will change
Which tests will be affected
```

For planned feature work, create an explicit implementation plan before editing.

---

# 21. Required Validation

After making changes:

```text
1. Run relevant tests.
2. Check the changed data grain.
3. Check for feature leakage where applicable.
4. Check API compatibility where applicable.
5. Review git diff.
6. Report what changed.
7. Report tests executed and their results.
```

Never claim that a test passed unless it was actually executed.

---

# 22. Important Analytical Principle

The system identifies:

```text
activity patterns
risk signals
anomalies
predictions
```

It does not automatically establish:

```text
actual network congestion
customer impact
root cause
```

unless the required evidence is available.

Keep analytical conclusions proportional to the available evidence.

---

# 23. Expected Claude Code Behaviour

Claude Code should behave as a careful engineering assistant.

It should:

* inspect before editing
* reuse existing logic
* preserve project conventions
* respect the canonical grain
* respect geography mapping
* prevent feature leakage
* avoid unsupported claims
* add tests for meaningful changes
* explain uncertainty
* keep changes focused

It should not:

* invent data
* invent endpoints
* invent model behaviour
* duplicate business logic
* silently alter raw data
* equate high activity with congestion
* treat a grid as a tower
* describe activity as counts or MB without evidence
* use future data in features
* make destructive changes without approval
