from pydantic import BaseModel, Field
from typing import List, Optional, Literal

Severity = Literal["Low", "Medium", "High", "Critical"]

class PredictIn(BaseModel):
    project: str = Field(..., description="Jira project key or internal project code")
    summary: str
    description: str

class PredictOut(BaseModel):
    category: str
    category_conf: float
    severity: Severity
    severity_conf: float
    assignee_top1: str
    assignee_top3: list[str]
    explanations: Optional[dict] = None
    model_version: str

class ExplainIn(BaseModel):
    text: str

class HealthOut(BaseModel):
    status: str = "ok"
    model_version: str
