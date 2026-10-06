# DE4 — Batch vs Streaming Decision Workshop

## 1. Decision Matrix

| Workload | Source | Arrival Pattern | Required Latency | Decision | Reason |
|---|---|---|---|---|---|
| Daily usage summary | Daily telecom activity CSV files | Once per day | Hours | **Batch** | The data arrives as daily files and real-time results are not required. |
| Hypothetical live activity events | Live network activity events | Continuous | Seconds/minutes | **Streaming** | Events would need to be processed as they arrive for near-real-time visibility. |
| Billing report | Billing/usage records | Periodic | Hours/days | **Batch** | Billing reports can be generated on a scheduled basis and do not require continuous processing. |
| Hotspot alerts | Network activity data | Continuous | Seconds/minutes | **Streaming** | Hotspot detection and alerts are time-sensitive and benefit from immediate processing. |
| Executive dashboard refresh | Processed analytics | Periodic | Minutes/hours | **Batch** | The executive dashboard does not require second-level updates for this training scenario. |
| Model training and scoring | Historical processed data | Scheduled | Hours | **Batch** | Model training uses accumulated historical data and can run as a scheduled job. |
| Real-time model scoring | Live network events | Continuous | Seconds | **Streaming** | Predictions need to be generated as new events arrive. |

---

## 2. Batch vs Streaming Decision

The training dataset is processed using **batch processing** because the telecom activity data is delivered as daily CSV files.

Although real network activity is continuous, the source available to this training pipeline is file-based and arrives in daily batches. Therefore, introducing streaming infrastructure would add operational complexity without providing a necessary latency benefit.

### Batch is appropriate for

- Daily usage summaries
- Billing reports
- Executive dashboard refreshes
- Model training
- Scheduled model scoring

### Streaming is appropriate for

- Live network activity monitoring
- Hotspot alerts
- Real-time model scoring

---

## 3. Optional Future Streaming Path

Kafka can conceptually enter the architecture when live network events become available.

Kafka is **not implemented or added to the current training dataset**. It is shown only as a possible future streaming path.

```text
                         CURRENT BATCH PATH
                              |
                    Daily Activity CSV Files
                              |
                              v
                       +--------------+
                       | Landing Zone |
                       +--------------+
                              |
                              v
                       +--------------+
                       | DE2 Ingestion|
                       +--------------+
                              |
                              v
                         Raw Zone
                              |
                              v
                       +--------------+
                       | Spark / SP7  |
                       +--------------+
                              |
                              v
                    Processed / Analytics
                              |
                              v
                          FastAPI
                              |
                              v
                           React
                              |
                              v
                         Consumers


                    OPTIONAL STREAMING PATH
                              |
                    Live Network Events
                              |
                              v
                         +--------+
                         | Kafka  |
                         +--------+
                              |
                              v
                    Stream Processing
                              |
                              v
                    Real-time ML Scoring
                              |
                              v
                       Alert / Risk
                              |
                              v
                          FastAPI
                              |
                              v
                           React
```

---

## 4. Batch Processing and Model Training

Batch processing is suitable for model training because training normally uses a historical collection of records rather than one event at a time.

The existing processed telecom data can therefore be used as input to scheduled model-training jobs.

A future real-time scoring system could use streaming events as input and produce predictions immediately.

```text
Historical Processed Data
          |
          v
   Batch ML Training
          |
          v
     Trained Model
          |
          |
          +----------------------+
                                 |
Live Network Events              |
          |                      |
          v                      |
        Kafka                    |
          |                      |
          v                      |
   Stream Processing             |
          |                      |
          v                      |
   Real-time ML Scoring <--------+
          |
          v
     Risk / Alerts
```

---

## 5. Engineering Decision

### Decision: Keep Daily Usage Summary as Batch

**Batch is the better engineering choice for the daily usage summary.**

The source data arrives as daily CSV files and the business requirement does not demand second-level latency. Batch processing with Spark is therefore simpler and sufficient.

Using Kafka and streaming processing for this workload would introduce additional infrastructure, monitoring, deployment, and operational complexity without providing a meaningful business benefit.

The engineering principle is:

> Choose the simplest architecture that satisfies the required latency and business need.

---

## 6. DE4 Scope

### In Scope

- Classifying workloads as batch or streaming
- Comparing latency requirements
- Identifying appropriate data sources and arrival patterns
- Showing where Kafka could conceptually enter the architecture
- Mapping batch processing to model training
- Mapping streaming to potential real-time scoring
- Defending an engineering decision

### Non-Goals

- Installing Kafka
- Building a streaming pipeline
- Changing the existing training dataset
- Implementing real-time scoring
- Replacing the existing Spark batch pipeline
