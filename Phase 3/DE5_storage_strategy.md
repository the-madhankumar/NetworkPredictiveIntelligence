# DE5 — Storage Strategy & Data Zones

## 1. Storage Strategy Table

| Zone | Data | Format | Write Semantics | Partitioning | Purpose |
|---|---|---|---|---|---|
| **Landing** | Incoming daily activity files | CSV | Append new incoming files | By incoming file/date | Temporary arrival area |
| **Raw** | Accepted activity files | CSV | Append; immutable after acceptance | By file/date | Preserve original accepted data for audit and reprocessing |
| **Reference** | `milano-grid.geojson` | GeoJSON | Controlled overwrite when intentionally replaced | **None** | Static reference data |
| **Processed** | Clean activity and Spark outputs | Parquet | Append new dates; controlled overwrite for rebuilds | **Date-partitioned** | Efficient processing and downstream consumption |
| **Analytics** | Curated summaries and warehouse tables | Parquet + warehouse tables | Append or controlled overwrite depending on output | By business requirement | BI, dashboards and analytical queries |
| **Logs** | Audit and execution history | CSV / log files | Append | Optional date-based organization | Operational traceability |



---

## 2. Data Zone Mapping

The pipeline uses separate zones so that incoming, accepted, transformed, reference, analytical and operational data have clear responsibilities.

```text
data/
├── landing/
│   ├── sms-call-internet-mi-2013-11-01.csv
│   ├── sms-call-internet-mi-2013-11-02.csv
│   └── ...
│
├── raw/
│   ├── sms-call-internet-mi-2013-11-01.csv
│   ├── sms-call-internet-mi-2013-11-02.csv
│   └── ...
│
├── reference/
│   └── milano-grid.geojson
│
├── processed/
│   └── activity/
│       ├── date=2013-11-01/
│       ├── date=2013-11-02/
│       ├── date=2013-11-03/
│       └── ...
│
├── analytics/
│   ├── hourly_grid_summary/
│   │   └── date=YYYY-MM-DD/
│   └── daily_grid_summary/
│       └── date=YYYY-MM-DD/
│
└── logs/
    ├── ingestion/
    └── pipeline/
```

### Partitioning Rules

- **Processed data is date-partitioned** to support efficient filtering and processing by date.
- **Reference data is not partitioned** because `milano-grid.geojson` is static reference data rather than daily activity data.
- Analytics partitioning depends on the analytical workload and query requirements.

---

## 3. Raw Data Immutability

Raw data is retained unchanged after acceptance.

The raw zone represents the original accepted source data and should not be modified by downstream cleaning or transformation processes.

Keeping raw data unchanged provides:

- Auditability
- Reproducibility
- Ability to reprocess data when transformation logic changes
- Ability to investigate data-quality issues
- Protection against losing the original source records

Cleaning and transformation should occur in downstream layers rather than modifying the raw copy.

---

## 4. Append vs Overwrite Semantics

### Landing

**Append**

New incoming daily files are added to the landing zone. Existing files should not be overwritten as part of normal ingestion.

### Raw

**Append / Immutable**

Accepted files are added to raw and remain unchanged. Existing raw records should not be modified.

### Reference

**Controlled overwrite**

The static reference can be replaced when an intentionally updated reference dataset is introduced. It does not participate in daily ingestion.

### Processed

**Append with controlled partition overwrite**

New dates can be appended. If a specific date needs to be rebuilt, only that partition may be intentionally overwritten.

### Analytics

**Append or controlled overwrite**

Historical analytical records can be appended. Recalculated summaries or partitions may be intentionally overwritten when the business logic requires a rebuild.

### Logs

**Append**

Execution and audit history should be retained rather than overwritten so that previous runs remain traceable.

---

## 5. Retention Considerations

### Raw Data

Raw data should be retained long enough to support:

- Auditing
- Reprocessing
- Troubleshooting
- Data-quality investigation
- Reproduction of historical pipeline results

The exact retention period should be determined by business, regulatory and storage requirements.

### Logs

Logs should be retained long enough to support:

- Failure investigation
- Operational troubleshooting
- Audit requirements
- Pipeline run history

Logs may have a shorter retention period than raw data depending on operational and compliance requirements.

---

## 6. Storage Contract

### Landing Contract

**Purpose:** Receive incoming daily telecom activity files.

**Expected format:** CSV.

**Expected data:** Daily `sms-call-internet-mi-YYYY-MM-DD.csv` activity files.

**Semantics:** Temporary incoming data. New files are appended.

---

### Raw Contract

**Purpose:** Store validated accepted source data.

**Expected format:** CSV.

**Semantics:** Immutable after acceptance. Raw data must remain unchanged.

**Requirement:** Only validated activity files should enter this zone.

---

### Reference Contract

**Purpose:** Store static reference data used for enrichment.

**Expected file:** `milano-grid.geojson`.

**Format:** GeoJSON.

**Semantics:** Static and non-partitioned. It does not pass through the daily ingestion flow.

---

### Processed Contract

**Purpose:** Store cleaned and transformed data for downstream processing.

**Format:** Parquet.

**Partitioning:** Date-partitioned.

**Semantics:** New date partitions are appended. Controlled partition overwrite is permitted for intentional rebuilds.

---

### Analytics Contract

**Purpose:** Store curated outputs for analytical consumption.

**Formats:** Warehouse tables and curated Parquet.

**Examples:**

- `hourly_grid_summary`
- `daily_grid_summary`
- Hotspot and risk outputs when implemented

**Semantics:** Append or controlled overwrite according to the specific analytical output.

---

### Logs Contract

**Purpose:** Maintain audit and pipeline execution history.

**Format:** CSV / log files.

**Semantics:** Append-oriented. Historical execution records should not be overwritten.

---

## 7. Design Principles

1. **Raw data is immutable.**
2. **Processed data uses Parquet for efficient analytical processing.**
3. **Processed activity data is partitioned by date.**
4. **Static reference data is kept separate and is not partitioned.**
5. **Each data zone has a clearly defined responsibility.**
6. **Append is the default behavior for accumulating historical data.**
7. **Overwrite is controlled and used only for intentional replacement or partition rebuilds.**
8. **Logs preserve operational history rather than replacing previous runs.**

---

## 8. Scope and Non-Goals

### In Scope

- Storage zones and their responsibilities
- File formats
- Partitioning strategy
- Raw immutability
- Append and overwrite semantics
- Retention considerations
- Storage contracts

### Non-Goals

- Implementing a cloud data lake
- Implementing a warehouse platform
- Changing the existing Spark processing logic
- Building a streaming storage architecture
- Implementing Kafka or Airflow
