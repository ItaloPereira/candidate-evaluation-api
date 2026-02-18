import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EvaluationCategory(str, enum.Enum):
    functionality = "functionality"
    code_quality = "code_quality"
    problem_solving = "problem_solving"
    communication = "communication"


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        UniqueConstraint("candidate_id", "category", name="uq_candidate_category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("candidates.id"), nullable=False
    )
    category: Mapped[EvaluationCategory] = mapped_column(
        Enum(EvaluationCategory), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    evaluator_notes: Mapped[str | None] = mapped_column(String, nullable=True)
    evaluated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
