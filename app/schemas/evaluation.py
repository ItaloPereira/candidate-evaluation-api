import enum
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.evaluation import EvaluationCategory


class Decision(str, enum.Enum):
    hire = "hire"
    needs_calibration = "needs_calibration"
    no_hire = "no_hire"


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


class CategoryScore(BaseModel):
    score: int | None
    weight: float
    weighted: float | None


class FinalScoreResponse(BaseModel):
    """
    Response model for the final score calculation endpoint.

    - If all 4 categories are evaluated: `final_score` contains the weighted sum,
      `partial_score` is None, and `decision` contains the hire recommendation.
    - If only some categories are evaluated: `partial_score` contains the weighted
      sum of available scores, `final_score` is None, and `decision` is None
      (no hiring decision can be made with incomplete evaluations).
    """

    candidate_id: int
    candidate_name: str
    final_score: float | None
    partial_score: float | None
    decision: Decision | None
    categories: dict[str, CategoryScore]
    evaluated_categories: int
    total_categories: int
