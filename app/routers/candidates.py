import math

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.evaluation import Evaluation
from app.schemas.candidate import CandidateCreate, CandidateResponse, CandidateUpdate
from app.models.evaluation import EvaluationCategory
from app.schemas.evaluation import (
    CategoryScore,
    Decision,
    EvaluationCreate,
    EvaluationResponse,
    FinalScoreResponse,
)

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(candidate_in: CandidateCreate, db: Session = Depends(get_db)):
    candidate = Candidate(
        email=candidate_in.email,
        first_name=candidate_in.first_name,
        last_name=candidate_in.last_name,
        status=candidate_in.status,
    )
    db.add(candidate)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A candidate with this email already exists",
        )
    db.refresh(candidate)
    return candidate


@router.get("", response_model=list[CandidateResponse])
def list_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).all()


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )
    return candidate


@router.put("/{candidate_id}", response_model=CandidateResponse)
def update_candidate(
    candidate_id: int, candidate_in: CandidateUpdate, db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    update_data = candidate_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(candidate, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A candidate with this email already exists",
        )
    db.refresh(candidate)
    return candidate


@router.post(
    "/{candidate_id}/evaluations",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_evaluation(
    candidate_id: int, evaluation_in: EvaluationCreate, db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    evaluation = Evaluation(
        candidate_id=candidate_id,
        category=evaluation_in.category,
        score=evaluation_in.score,
        evaluator_notes=evaluation_in.evaluator_notes,
    )
    db.add(evaluation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An evaluation for this category already exists for this candidate",
        )
    db.refresh(evaluation)
    return evaluation


@router.get("/{candidate_id}/evaluations", response_model=list[EvaluationResponse])
def list_evaluations(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    return db.query(Evaluation).filter(Evaluation.candidate_id == candidate_id).all()


CATEGORY_WEIGHTS: dict[EvaluationCategory, float] = {
    EvaluationCategory.functionality: 0.40,
    EvaluationCategory.code_quality: 0.25,
    EvaluationCategory.problem_solving: 0.20,
    EvaluationCategory.communication: 0.15,
}

TOTAL_CATEGORIES = len(CATEGORY_WEIGHTS)


@router.get("/{candidate_id}/final-score", response_model=FinalScoreResponse)
def get_final_score(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    evaluations = (
        db.query(Evaluation).filter(Evaluation.candidate_id == candidate_id).all()
    )

    if not evaluations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No evaluations exist for this candidate",
        )

    eval_by_category = {e.category: e.score for e in evaluations}

    categories: dict[str, CategoryScore] = {}
    weighted_sum = 0.0

    for category, weight in CATEGORY_WEIGHTS.items():
        score = eval_by_category.get(category)
        if score is not None:
            weighted = math.ceil(score * weight * 100) / 100
            weighted_sum += weighted
        else:
            weighted = None
        categories[category.value] = CategoryScore(
            score=score, weight=weight, weighted=weighted
        )

    evaluated_count = len(eval_by_category)
    candidate_name = f"{candidate.first_name} {candidate.last_name}"

    if evaluated_count == TOTAL_CATEGORIES:
        final_score = round(weighted_sum, 2)
        if final_score >= 4.0:
            decision = Decision.hire
        elif final_score >= 3.0:
            decision = Decision.needs_calibration
        else:
            decision = Decision.no_hire
        return FinalScoreResponse(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            final_score=final_score,
            partial_score=None,
            decision=decision,
            categories=categories,
            evaluated_categories=evaluated_count,
            total_categories=TOTAL_CATEGORIES,
        )
    else:
        partial_score = round(weighted_sum, 2)
        return FinalScoreResponse(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            final_score=None,
            partial_score=partial_score,
            decision=None,
            categories=categories,
            evaluated_categories=evaluated_count,
            total_categories=TOTAL_CATEGORIES,
        )
