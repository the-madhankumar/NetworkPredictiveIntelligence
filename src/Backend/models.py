from typing import List, Optional

from pydantic import BaseModel, Field
from datetime import datetime

class NetworkSummaryResponse(BaseModel):
    as_of: datetime
    total_activity: float
    active_grids: int
    peak_hour: int
    top_grid: int

class ActivityPoint(BaseModel):
    timestamp: datetime
    sms_in: float
    sms_out: float
    call_in: float
    call_out: float
    internet_activity: float
    total_sms: float
    total_calls: float
    total_activity: float
    internet_share: float

class GridActivityResponse(BaseModel):
    grid_id: int
    as_of: datetime
    date: Optional[datetime] = None
    hour: Optional[int] = None
    data: list[ActivityPoint]

class HotspotItem(BaseModel):
    grid_id: int
    timestamp: datetime
    total_activity: float
    sms_activity: float
    call_activity: float
    internet_activity: float
    status: str
    severity: str
    reason: str
    risk: Optional[float] = None
    risk_label: Optional[str] = None
    model_version: Optional[str] = None


class AlertItem(BaseModel):
    grid_id: int
    timestamp: datetime
    total_activity: float
    sms_activity: float
    call_activity: float
    internet_activity: float
    status: str
    severity: str
    reason: str
    risk: Optional[float] = None
    risk_label: Optional[str] = None
    model_version: Optional[str] = None


class NetworkItemsResponse(BaseModel):
    as_of: datetime
    limit: int
    data: list[HotspotItem]


class HotspotItem(BaseModel):
    grid_id: int
    timestamp: datetime
    total_activity: float
    sms_activity: float
    call_activity: float
    internet_activity: float
    status: str
    severity: str
    reason: str
    risk: Optional[float] = None
    risk_label: Optional[str] = None
    model_version: Optional[str] = None


class AlertItem(BaseModel):
    grid_id: int
    timestamp: datetime
    total_activity: float
    sms_activity: float
    call_activity: float
    internet_activity: float
    status: str
    severity: str
    reason: str
    risk: Optional[float] = None
    risk_label: Optional[str] = None
    model_version: Optional[str] = None


class NetworkItemsResponse(BaseModel):
    as_of: datetime
    limit: int
    data: list[HotspotItem]


class GridFeatureValues(BaseModel):
    avg_activity: float
    activity_growth: float
    active_hours: float
    peak_ratio: float
    variability: float
    internet_share: float


class GridFeatureResponse(BaseModel):
    grid_id: int
    feature_timestamp: datetime
    features: GridFeatureValues
    data_quality: str
    feature_freshness: str

class RiskPredictionRequest(BaseModel):
    grid_id: int = Field(..., ge=1, le=10000)
    as_of: Optional[str] = None


class RiskPredictionResponse(BaseModel):
    grid_id: int
    as_of: Optional[str]
    risk_score: float
    risk_level: str
    model_version: str
    explanation_note: str

# Assistant


class ConversationMessage(BaseModel):
    role: str
    content: str

class AssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_history: list[ConversationMessage] = Field(
        default_factory=list
    )
    thinking: bool = False
    use_cache: bool = True


class AssistantChatResponse(BaseModel):
    reply: str
    model: str
    thinking_enabled: bool
    cache_enabled: bool
    usage: dict[str, int]

class TaskStatus(BaseModel):
    task_name: str
    status: str
    rows_in: int
    rows_rejected: int
    nulls_handled: int
    rows_published: int


class PipelineStatusResponse(BaseModel):
    healthy: bool
    reasons: List[str]
    last_run_id: str
    last_run_timestamp: datetime
    as_of: datetime
    freshness: str
    tasks: List[TaskStatus]


class ExplainPredictionRequest(BaseModel):
    grid_id: int = Field(..., description="Target grid cell ID")
    as_of: str = Field(..., description="Timestamp of the feature data used")
    risk_score: float = Field(..., description="Risk score output from /network/predict-risk")
    risk_level: str = Field(..., description="Risk level ('high' or 'low')")
    model_version: str = Field(..., description="ML model version used")
    explanation_note: Optional[str] = Field(None, description="System note from predict_risk")

class ExplainPredictionResponse(BaseModel):
    grid_id: int
    risk_level: str
    risk_score: float
    explanation: str
    location_summary: Optional[dict] = None