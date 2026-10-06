from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import ExplainPredictionRequest, ExplainPredictionResponse
from schemas import DimGrid
from service.assistant import chat
from fastapi import APIRouter, Depends, HTTPException

assistant_router = APIRouter(
    prefix="/assistant",
    tags=["Assistant / Operational Support"],
)

@assistant_router.post(
    "/explain-prediction",
    response_model=ExplainPredictionResponse,
    summary="Explain a Single Grid Risk Prediction",
)
def explain_single_prediction(
    request: ExplainPredictionRequest,
    db: Session = Depends(get_db),
) -> ExplainPredictionResponse:
    try:
        grid = (
            db.query(DimGrid).filter(DimGrid.grid_id == request.grid_id).first()
        )

        location_info = None
        if grid:
            location_info = {
                "centroid_lat": float(grid.centroid_latitude),
                "centroid_lon": float(grid.centroid_longitude),
                "polygon_ref": getattr(
                    grid, "polygon_ref", f"poly_grid_{request.grid_id}"
                ),
            }

        prompt = (
            f"EXPLAIN THIS PREDICTION RESULT:\n"
            f"- Grid ID: {request.grid_id}\n"
            f"- Risk Level: {request.risk_level.upper()}\n"
            f"- Risk Score: {request.risk_score}\n"
            f"- Feature Timestamp (As Of): {request.as_of}\n"
            f"- Model Version: {request.model_version}\n"
            f"- Location Context: {location_info if location_info else 'N/A'}\n"
            f"- Model Note: {request.explanation_note or 'N/A'}\n\n"
            f"Write a concise, 2-3 sentence operational explanation detailing why Grid {request.grid_id} "
            f"has been flagged as {request.risk_level.upper()} risk and what immediate action "
            f"the network operations team should take."
        )

        ai_response = chat(
            message=prompt,
            conversation_history=[],
            thinking=False,
            use_cache=True,
        )

        if isinstance(ai_response, dict):
            explanation_text = (
                ai_response.get("content")
                or ai_response.get("message")
                or str(ai_response)
            )
        else:
            explanation_text = str(ai_response)

        return ExplainPredictionResponse(
            grid_id=request.grid_id,
            risk_level=request.risk_level,
            risk_score=request.risk_score,
            explanation=explanation_text,
            location_summary=location_info,
        )

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "authentication_error" in error_msg:
            raise HTTPException(
                status_code=502,
                detail="LLM Service Authentication Error: ANTHROPIC_API_KEY is invalid or missing.",
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate prediction explanation: {error_msg}",
        )