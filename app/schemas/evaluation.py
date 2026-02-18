from datetime import datetime

from pydantic import BaseModel, Field

from app.models.evaluation import EvaluationCategory


class EvaluationCreate(BaseModel):
    category: EvaluationCategory
    score: int = Field(..., ge=1, le=5)
    evaluator_notes: str | None = None


class EvaluationResponse(BaseModel):
    id: int
    candidate_id: int
    category: EvaluationCategory
    score: int
    evaluator_notes: str | None
    evaluated_at: datetime

    model_config = {"from_attributes": True}
