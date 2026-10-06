import datetime
import sys
from pathlib import Path
import yaml
import time

SRC_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC_DIR))

from AirFlow.dags.Phase3.DE8.de8_pipeline_service import run_pipeline

import pandas as pd


HOURLY_GRID_PATH = "../../../Dataset/analytics/hourly_grid_summary.parquet"
NETWORK_FEATURE_PATH = "../../../Dataset/analytics/ML_LAYER/network_feature_table.parquet"
ANOMALY_PATH = "../../../Dataset/analytics/ML_LAYER/anomaly_detection/network_anomaly_scores.parquet"
ALERTS_PATH = "../../../Dataset/landing/alerts.csv"

def load_config(config_path: str) -> dict:

    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_file}"
        )

    with open(config_file, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not config:
        raise ValueError(
            f"Configuration file is empty: {config_file}"
        )

    return config

def _get_first_row(df: pd.DataFrame) -> pd.Series | None:
    if df.empty:
        return None

    return df.iloc[0]


def _get_value(row: pd.Series | None, column: str, default=None):
    if row is None or column not in row:
        return default

    value = row[column]

    if pd.isna(value):
        return default

    return value

def get_long_context_incident(
    grid_id: int,
    timestamp: datetime.datetime | str,
):
    start_time = time.perf_counter()
    timestamp = pd.Timestamp(timestamp)
    timestamp = timestamp.floor("h")
    hourly_grid_summary = pd.read_parquet(HOURLY_GRID_PATH)

    hourly_grid_summary["timestamp"] = pd.to_datetime(
        hourly_grid_summary["timestamp"]
    ).dt.floor("h")

    current = hourly_grid_summary[
        (hourly_grid_summary["grid_id"] == grid_id)
        & (hourly_grid_summary["timestamp"] == timestamp)
    ]

    current = _get_first_row(current)

    if current is None:
        return None
    
    network_feature = pd.read_parquet(NETWORK_FEATURE_PATH)

    network_feature["feature_timestamp"] = pd.to_datetime(
        network_feature["feature_timestamp"]
    ).dt.floor("h")

    features = network_feature[
        (network_feature["grid_id"] == grid_id)
        & (network_feature["feature_timestamp"] == timestamp)
    ]

    features = _get_first_row(features)

    anomaly_df = pd.read_parquet(ANOMALY_PATH)

    anomaly_df["timestamp"] = pd.to_datetime(
        anomaly_df["timestamp"]
    ).dt.floor("h")

    anomaly = anomaly_df[
        (anomaly_df["grid_id"] == grid_id)
        & (anomaly_df["timestamp"] == timestamp)
    ]

    anomaly = _get_first_row(anomaly)

    alerts_df = pd.read_csv(ALERTS_PATH)

    alerts_df["timestamp"] = pd.to_datetime(
        alerts_df["timestamp"]
    ).dt.floor("h")

    historical_alerts = alerts_df[
        alerts_df["grid_id"] == grid_id
    ]

    total_alerts = len(historical_alerts)

    activity_drop_events = (
        historical_alerts["alert_type"]
        .eq("ACTIVITY_DROP")
        .sum()
    )

    high_activity_events = (
        historical_alerts["alert_type"]
        .eq("HIGH_ACTIVITY")
        .sum()
    )

    current_alerts = historical_alerts[
        historical_alerts["timestamp"] == timestamp
    ]

    current_total_alerts = len(current_alerts)

    current_activity_drop_events = (
        current_alerts["alert_type"]
        .eq("ACTIVITY_DROP")
        .sum()
    )

    current_high_activity_events = (
        current_alerts["alert_type"]
        .eq("HIGH_ACTIVITY")
        .sum()
    )

    config = load_config("./config.yaml")

    context = {
        "grid_id": grid_id,

        "current": {
            "timestamp": timestamp,
            "activity": _get_value(
                current,
                "total_activity",
            ),
        },

        "features": {
            "activity_growth": _get_value(
                features,
                "activity_growth",
            ),
            "peak_ratio": _get_value(
                features,
                "peak_ratio",
            ),
            "variability": _get_value(
                features,
                "variability",
            ),
            "internet_share": _get_value(
                features,
                "internet_share",
            ),
        },

        "anomaly": {
            "score": _get_value(
                anomaly,
                "anomaly_score",
            ),
            "direction": _get_value(
                anomaly,
                "direction",
            ),
        },

        "alerts": {
            "current": {
                "total_alerts": int(current_total_alerts),
                "activity_drop_events": int(
                    current_activity_drop_events
                ),
                "high_activity_events": int(
                    current_high_activity_events
                ),
            },

            "historical": {
                "total_alerts": int(total_alerts),
                "activity_drop_events": int(
                    activity_drop_events
                ),
                "high_activity_events": int(
                    high_activity_events
                ),
            },
        },

        "pipeline_status": run_pipeline(config)
    }

    elapsed_time = time.perf_counter() - start_time
    
    context["pipeline_status"]["total_time_seconds"] = round( elapsed_time, 4, )

    return context

context = get_long_context_incident(
    grid_id=1,
    timestamp="2013-11-01T00:00:00",
)

print(context)
