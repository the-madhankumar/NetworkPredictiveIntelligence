# AI Engineering Review

Review code changes against the Network Operations and Predictive Intelligence project rules.

The review is advisory only.

Never approve, merge, deploy, commit, reset, or modify project files.

## Review Categories

### 1. Data Grain

Check that analytics data maintains exactly one record per:

`grid_id + timestamp`

Identify:

* duplicate records
* incorrect aggregation
* accidental row multiplication
* incorrect joins

### 2. Feature Leakage

Check that every feature at:

`feature_timestamp`

uses only information available at or before that timestamp.

Flag:

* future activity
* future labels
* future aggregates
* current-period leakage into baseline
* target leakage

### 3. Geographic Join

The canonical geographic mapping is:

`properties.cellId -> grid_id`

Check for:

* incorrect geographic keys
* joins on unrelated identifiers
* missing geographic records
* duplicated geographic matches

### 4. API Contract

API changes should be additive whenever possible.

Check:

* response compatibility
* removed fields
* renamed fields
* changed data types
* undocumented fields
* frontend-breaking changes

### 5. Terminology

Do not make unsupported claims.

Activity must not automatically be described as:

* counts
* MB
* confirmed congestion

A grid is a geographic cell.

A high activity value alone does not prove congestion.

### 6. Tests

Check whether the change includes appropriate tests.

Prioritize:

* grain tests
* leakage tests
* API contract tests
* geography tests
* anomaly/risk tests
* pipeline tests

## Output

Return:

## STATUS

PASS or WARN or FAIL

## DATA GRAIN

Findings.

## FEATURE LEAKAGE

Findings.

## GEOGRAPHIC JOIN

Findings.

## API CONTRACT

Findings.

## TERMINOLOGY

Findings.

## TEST COVERAGE

Findings.

## MISSED BY TESTS

Identify at least one issue that static/unit tests may not detect, or explicitly state that no additional issue was found.

## RECOMMENDATION

Recommended next engineering actions.

Do not approve or merge the change.
