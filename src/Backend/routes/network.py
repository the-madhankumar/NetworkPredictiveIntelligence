from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
import joblib
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from service.service import build_item, get_activity_rows, get_as_of
from models import GridFeatureResponse, GridFeatureValues, NetworkItemsResponse, NetworkSummaryResponse, GridActivityResponse, ActivityPoint, PipelineStatusResponse, RiskPredictionRequest, RiskPredictionResponse, TaskStatus
from database import get_db
from schemas import DimTime, DimGrid, FactNetworkActivity

network_router = APIRouter()

network_anamoly_parquet = pd.read_parquet(
    "../../Dataset/analytics/ML_LAYER/anomaly_detection/network_anomaly_scores.parquet"
)
hourly_grid_summary = pd.read_parquet(
    "../../Dataset/analytics/hourly_grid_summary.parquet"
)

@network_router.get(
    "/network/summary",
    response_model=NetworkSummaryResponse
)
def network_summary(
    as_of: Optional[datetime] = Query(
        default=None
    ),
    db: Session = Depends(get_db)
):
    try:
        if as_of is None:
            effective_as_of = db.query(
                func.max(DimTime.timestamp)
            ).scalar()

            if effective_as_of is None:
                raise HTTPException(
                    status_code=500,
                    detail="Analytics data source is unavailable or empty."
                )
        else:
            effective_as_of = as_of

        total_activity = (
            db.query(
                func.sum(
                    FactNetworkActivity.total_activity
                )
            )
            .join(
                DimTime,
                FactNetworkActivity.time_key == DimTime.time_key
            )
            .filter(
                DimTime.timestamp <= effective_as_of
            )
            .scalar()
        )

        active_grids = (
            db.query(
                func.count(
                    func.distinct(
                        FactNetworkActivity.grid_id
                    )
                )
            )
            .join(
                DimTime,
                FactNetworkActivity.time_key == DimTime.time_key
            )
            .filter(
                DimTime.timestamp <= effective_as_of
            )
            .scalar()
        )

        peak_hour_result = (
            db.query(
                DimTime.hour_value,
                func.sum(
                    FactNetworkActivity.total_activity
                ).label("activity")
            )
            .join(
                DimTime,
                FactNetworkActivity.time_key == DimTime.time_key
            )
            .filter(
                DimTime.timestamp <= effective_as_of
            )
            .group_by(
                DimTime.hour_value
            )
            .order_by(
                func.sum(
                    FactNetworkActivity.total_activity
                ).desc()
            )
            .first()
        )

        top_grid_result = (
            db.query(
                FactNetworkActivity.grid_id,
                func.sum(
                    FactNetworkActivity.total_activity
                ).label("activity")
            )
            .join(
                DimTime,
                FactNetworkActivity.time_key == DimTime.time_key
            )
            .filter(
                DimTime.timestamp <= effective_as_of
            )
            .group_by(
                FactNetworkActivity.grid_id
            )
            .order_by(
                func.sum(
                    FactNetworkActivity.total_activity
                ).desc()
            )
            .first()
        )

        if total_activity is None:
            raise HTTPException(
                status_code=500,
                detail="No analytics data available."
            )

        if peak_hour_result is None:
            raise HTTPException(
                status_code=500,
                detail="Unable to determine peak hour."
            )

        if top_grid_result is None:
            raise HTTPException(
                status_code=500,
                detail="Unable to determine top grid."
            )

        return NetworkSummaryResponse(
            as_of=effective_as_of,
            total_activity=float(total_activity),
            active_grids=int(active_grids or 0),
            peak_hour=int(peak_hour_result.hour_value),
            top_grid=int(top_grid_result.grid_id)
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Analytics data source unavailable: {str(error)}"
        )

@network_router.get("/network/grid/{grid_id}", response_model=GridActivityResponse)
def network_grid(
    grid_id: int,
    date: Optional[datetime] = Query(None),
    hour: Optional[int] = Query(None, ge=0, le=23),
    as_of: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        if grid_id < 1 or grid_id > 10000:
            raise HTTPException(status_code=404, detail="Grid not found")

        grid_exists = db.query(DimGrid.grid_id).filter(
            DimGrid.grid_id == grid_id
        ).first()

        if not grid_exists:
            raise HTTPException(status_code=404, detail="Grid not found")

        effective_as_of = as_of or db.query(
            func.max(DimTime.timestamp)
        ).scalar()

        if effective_as_of is None:
            raise HTTPException(
                status_code=500,
                detail="Analytics data source unavailable"
            )

        if date is not None:
            effective_as_of = effective_as_of.replace(
                year=date.year,
                month=date.month,
                day=date.day
            )

        if hour is not None:
            effective_as_of = effective_as_of.replace(hour=hour)

        start_time = effective_as_of - timedelta(hours=23)

        rows = (
            db.query(
                DimTime.timestamp,
                FactNetworkActivity.sms_in,
                FactNetworkActivity.sms_out,
                FactNetworkActivity.call_in,
                FactNetworkActivity.call_out,
                FactNetworkActivity.internet_activity
            )
            .join(
                DimTime,
                FactNetworkActivity.time_key == DimTime.time_key
            )
            .filter(
                FactNetworkActivity.grid_id == grid_id,
                DimTime.timestamp >= start_time,
                DimTime.timestamp <= effective_as_of
            )
            .order_by(DimTime.timestamp)
            .all()
        )

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No activity data found for grid {grid_id}"
            )

        data = []

        for row in rows:
            sms_in = float(row.sms_in or 0)
            sms_out = float(row.sms_out or 0)
            call_in = float(row.call_in or 0)
            call_out = float(row.call_out or 0)
            internet = float(row.internet_activity or 0)

            total_sms = sms_in + sms_out
            total_calls = call_in + call_out
            total_activity = total_sms + total_calls + internet
            internet_share = (
                internet / total_activity
                if total_activity > 0
                else 0.0
            )

            data.append(
                ActivityPoint(
                    timestamp=row.timestamp,
                    sms_in=sms_in,
                    sms_out=sms_out,
                    call_in=call_in,
                    call_out=call_out,
                    internet_activity=internet,
                    total_sms=total_sms,
                    total_calls=total_calls,
                    total_activity=total_activity,
                    internet_share=internet_share
                )
            )

        return GridActivityResponse(
            grid_id=grid_id,
            as_of=effective_as_of,
            date=date,
            hour=hour,
            data=data
        )

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Analytics data source unavailable: {error}"
        )

@network_router.get("/network/hotspots", response_model=NetworkItemsResponse)
def hotspots(
    limit: int = Query(10, ge=1, le=100),
    severity: Optional[str] = Query(None),
    as_of: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        effective_as_of = get_as_of(db, as_of)
        rows = get_activity_rows(db, effective_as_of, limit)

        if severity:
            severity = severity.lower()
            if severity not in {"low", "medium", "high", "critical"}:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid severity"
                )

        data = []

        for row in rows:
            total = float(row.total_activity or 0)

            if total >= 10000:
                level = "critical"
                reason = "Extremely high network activity detected."
            elif total >= 5000:
                level = "high"
                reason = "High network activity detected."
            elif total >= 1000:
                level = "medium"
                reason = "Elevated network activity detected."
            else:
                level = "low"
                reason = "Normal network activity."

            if severity and level != severity:
                continue

            data.append(build_item(row, level, reason))

        return {
            "as_of": effective_as_of,
            "limit": limit,
            "data": data
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Analytics data source unavailable: {error}"
        )

@network_router.get("/network/alerts", response_model=NetworkItemsResponse)
def alerts(
    limit: int = Query(10, ge=1, le=100),
    severity: Optional[str] = Query(None),
    as_of: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        effective_as_of = get_as_of(db, as_of)
        rows = get_activity_rows(db, effective_as_of, limit)

        if severity:
            severity = severity.lower()
            if severity not in {"low", "medium", "high", "critical"}:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid severity"
                )

        data = []

        for row in rows:
            total = float(row.total_activity or 0)

            if total >= 10000:
                level = "critical"
                reason = "Critical network activity threshold exceeded."
            elif total >= 5000:
                level = "high"
                reason = "High network activity threshold exceeded."
            elif total >= 1000:
                level = "medium"
                reason = "Elevated network activity threshold exceeded."
            else:
                level = "low"
                reason = "No significant network activity anomaly."

            if severity and level != severity:
                continue

            data.append(build_item(row, level, reason))

        return {
            "as_of": effective_as_of,
            "limit": limit,
            "data": data
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Analytics data source unavailable: {error}"
        )

@network_router.get(
    "/network/grid/{grid_id}/features",
    response_model=GridFeatureResponse
)
def get_grid_features(
    grid_id: int,
    as_of: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        if grid_id < 1 or grid_id > 10000:
            raise HTTPException(
                status_code=404,
                detail="Grid not found"
            )

        grid_exists = (
            db.query(DimGrid.grid_id)
            .filter(DimGrid.grid_id == grid_id)
            .first()
        )

        if not grid_exists:
            raise HTTPException(
                status_code=404,
                detail="Grid not found"
            )

        effective_as_of = as_of or db.query(
            func.max(DimTime.timestamp)
        ).scalar()

        if effective_as_of is None:
            raise HTTPException(
                status_code=500,
                detail="Analytics data source unavailable"
            )

        start_time = effective_as_of - timedelta(hours=23)

        rows = (
            db.query(
                DimTime.timestamp,
                FactNetworkActivity.total_activity,
                FactNetworkActivity.internet_activity
            )
            .join(
                DimTime,
                FactNetworkActivity.time_key == DimTime.time_key
            )
            .filter(
                FactNetworkActivity.grid_id == grid_id,
                DimTime.timestamp >= start_time,
                DimTime.timestamp <= effective_as_of
            )
            .order_by(DimTime.timestamp)
            .all()
        )

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No activity data found for grid {grid_id}"
            )

        activities = [
            float(row.total_activity or 0)
            for row in rows
        ]

        internet_values = [
            float(row.internet_activity or 0)
            for row in rows
        ]

        avg_activity = sum(activities) / len(activities)

        peak_activity = max(activities)

        peak_ratio = (
            peak_activity / avg_activity
            if avg_activity > 0
            else 0.0
        )

        active_hours = sum(
            1 for value in activities if value > 0
        )

        total_activity = sum(activities)
        total_internet = sum(internet_values)

        internet_share = (
            total_internet / total_activity
            if total_activity > 0
            else 0.0
        )

        if len(activities) > 1 and avg_activity > 0:
            mean = avg_activity
            variance = sum(
                (value - mean) ** 2
                for value in activities
            ) / len(activities)

            variability = variance ** 0.5 / mean
        else:
            variability = 0.0

        if len(activities) >= 2:
            previous = activities[:-1]
            previous_avg = sum(previous) / len(previous)

            activity_growth = (
                (activities[-1] - previous_avg) / previous_avg
                if previous_avg > 0
                else 0.0
            )
        else:
            activity_growth = 0.0

        data_quality = "valid"

        if len(rows) < 24:
            data_quality = "incomplete"

        latest_timestamp = rows[-1].timestamp

        if latest_timestamp >= effective_as_of:
            feature_freshness = "fresh"
        elif effective_as_of - latest_timestamp <= timedelta(hours=3):
            feature_freshness = "stale"
        else:
            feature_freshness = "very_stale"

        return GridFeatureResponse(
            grid_id=grid_id,
            feature_timestamp=latest_timestamp,
            features=GridFeatureValues(
                avg_activity=avg_activity,
                activity_growth=activity_growth,
                active_hours=active_hours,
                peak_ratio=peak_ratio,
                variability=variability,
                internet_share=internet_share
            ),
            data_quality=data_quality,
            feature_freshness=feature_freshness
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Analytics data source unavailable: {error}"
        )

MODEL_PATH = Path("../../Dataset/analytics/ML_LAYER/risk_classifier/risk_classifier.joblib")
FEATURE_PATH = Path("../../Dataset/analytics/ML_LAYER/network_feature_table.parquet")

FEATURE_COLUMNS = [
    "avg_activity",
    "activity_growth",
    "active_hours",
    "peak_ratio",
    "variability",
    "internet_share",
]

try:
    risk_model = joblib.load(MODEL_PATH)
    model_version = "risk-classifier-logistic-regression-v1"
except Exception as e:
    raise RuntimeError(f"Failed to load ML5 model from {MODEL_PATH}: {e}")

@network_router.post(
    "/network/predict-risk",
    response_model=RiskPredictionResponse
)
def predict_risk(request: RiskPredictionRequest):
    try:
        features = pd.read_parquet(FEATURE_PATH)

        features["feature_timestamp"] = pd.to_datetime(
            features["feature_timestamp"]
        )

        grid_features = features[
            features["grid_id"] == request.grid_id
        ].copy()

        if grid_features.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No feature data found for grid_id {request.grid_id}"
            )

        if request.as_of:
            as_of = pd.to_datetime(request.as_of)
            grid_features = grid_features[
                grid_features["feature_timestamp"] <= as_of
            ]

        if grid_features.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No feature data available for grid_id {request.grid_id} at requested as_of"
            )

        latest = grid_features.sort_values(
            "feature_timestamp"
        ).iloc[-1]

        missing_features = [
            column
            for column in FEATURE_COLUMNS
            if column not in latest.index
        ]

        if missing_features:
            raise HTTPException(
                status_code=500,
                detail=f"ML2 feature schema mismatch. Missing features: {missing_features}"
            )

        model_input = pd.DataFrame(
            [[latest[column] for column in FEATURE_COLUMNS]],
            columns=FEATURE_COLUMNS
        )

        prediction = risk_model.predict(model_input)[0]

        if hasattr(risk_model, "predict_proba"):
            probabilities = risk_model.predict_proba(model_input)[0]
            risk_score = float(max(probabilities))
        else:
            risk_score = float(prediction)

        risk_level = "high" if prediction == 1 else "low"

        return RiskPredictionResponse(
            grid_id=request.grid_id,
            as_of=latest["feature_timestamp"].isoformat(),
            risk_score=round(risk_score, 4),
            risk_level=risk_level,
            model_version=model_version,
            explanation_note=f"Prediction generated using ML5 trained risk classifier from ML2 features at {latest['feature_timestamp'].isoformat()}."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Risk prediction failed: {str(e)}"
        )


@network_router.post("/network/anamoly_score")
def get_anamoly_score(
    grid_id: int,
    timestamp: datetime
):
    rows = network_anamoly_parquet[
        (network_anamoly_parquet["grid_id"] == grid_id)
        & (network_anamoly_parquet["timestamp"] == timestamp)
    ]

    if rows.empty:
        raise HTTPException(
            status_code=404,
            detail="No anomaly score found"
        )

    row = rows.iloc[0]

    return {
        "grid_id": int(row["grid_id"]),
        "anomaly_score": float(row["anomaly_score"]),
    }


@network_router.post("/network/total_activity")
def get_total_activity_score(
    grid_id: int
):
    rows = hourly_grid_summary[
        (hourly_grid_summary["grid_id"] == grid_id)
    ]

    if rows.empty:
        raise HTTPException(
            status_code=404,
            detail="No anomaly score found"
        )

    row = rows.iloc[0]

    return {
        "grid_id": int(row["grid_id"]),
        "total_activity": float(row["total_activity"]),
    }

QUALITY_CHECK_LOG_PATH = (
    Path(r"D:\Training Project\Project 2\Dataset\analytics\DE7\quality_check_status.json")
)

@network_router.get(
    "/pipeline/status",
    response_model=PipelineStatusResponse,
    tags=["Operational Support"],
)
def get_pipeline_status():
    if not QUALITY_CHECK_LOG_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="Pipeline status record is unavailable or has not been generated by DE7 yet.",
        )

    try:
        with open(QUALITY_CHECK_LOG_PATH, "r", encoding="utf-8") as f:
            status_data = json.load(f)

        last_run_id = status_data.get("run_id", "UNKNOWN_RUN")

        # Parse timestamps into datetime objects
        last_run_ts = datetime.fromisoformat(
            status_data.get(
                "timestamp", datetime.now(timezone.utc).isoformat()
            )
        )
        as_of = datetime.fromisoformat(
            status_data.get("as_of", datetime.now(timezone.utc).isoformat())
        )

        tasks = [TaskStatus(**task) for task in status_data.get("tasks", [])]

        reasons = []
        healthy = True

        # Check 1: Verify overall status flag or individual task failures
        if status_data.get("overall_status") != "PASS":
            healthy = False

        for task in tasks:
            if task.status.upper() not in {"PASS", "SUCCESS"}:
                healthy = False
                reasons.append(f"Task '{task.task_name}' failed or halted.")

        # Check 2: Evaluate data rejection anomalies
        total_rejected = sum(t.rows_rejected for t in tasks)
        total_published = sum(t.rows_published for t in tasks)

        if total_published == 0 and len(tasks) > 0:
            healthy = False
            reasons.append(
                "Pipeline published 0 rows to the analytics storage layer."
            )

        if total_published > 0 and (total_rejected / total_published) > 0.15:
            healthy = False
            reasons.append(
                f"High row rejection rate detected ({total_rejected} rows rejected)."
            )

        # Check 3: Calculate analytics layer freshness
        now = datetime.now(timezone.utc)
        ts_for_calc = (
            last_run_ts
            if last_run_ts.tzinfo
            else last_run_ts.replace(tzinfo=timezone.utc)
        )
        age_hours = (now - ts_for_calc).total_seconds() / 3600.0

        if age_hours <= 1.0:
            freshness = "fresh"
        elif age_hours <= 3.0:
            freshness = "stale"
        else:
            freshness = "critical"
            healthy = False
            reasons.append(
                f"Analytics data layer is stale. Last pipeline run was {age_hours:.1f} hours ago."
            )

        return PipelineStatusResponse(
            healthy=healthy,
            reasons=reasons,
            last_run_id=last_run_id,
            last_run_timestamp=last_run_ts,
            as_of=as_of,
            freshness=freshness,
            tasks=tasks,
        )

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading pipeline status record: {str(error)}",
        )