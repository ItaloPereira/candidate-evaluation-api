import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate, CandidateStatus
from app.models.evaluation import Evaluation, EvaluationCategory
from app.schemas.candidate import (
    CandidateCreate,
    CandidateListItem,
    CandidateListResponse,
    CandidateResponse,
    CandidateUpdate,
)
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


@router.get("", response_model=CandidateListResponse)
def list_candidates(
    status: CandidateStatus | None = None,
    min_score: float | None = Query(default=None, ge=0, le=5),
    max_score: float | None = Query(default=None, ge=0, le=5),
    sort_by: str = Query(default="created_at", pattern="^(created_at|final_score|last_name)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1),
    db: Session = Depends(get_db),
):
    per_page = min(per_page, 100)

    query = db.query(Candidate)
    if status is not None:
        query = query.filter(Candidate.status == status)

    candidates = query.all()

    all_evaluations = db.query(Evaluation).all()
    evals_by_candidate: dict[int, list[Evaluation]] = {}
    for e in all_evaluations:
        evals_by_candidate.setdefault(e.candidate_id, []).append(e)

    results: list[tuple[Candidate, float | None]] = []
    for candidate in candidates:
        candidate_evals = evals_by_candidate.get(candidate.id, [])
        final_score = calculate_final_score(candidate_evals)

        if min_score is not None or max_score is not None:
            if final_score is None:
                continue
            if min_score is not None and final_score < min_score:
                continue
            if max_score is not None and final_score > max_score:
                continue

        results.append((candidate, final_score))

    reverse = sort_order == "desc"
    if sort_by == "final_score":
        results.sort(
            key=lambda x: (x[1] is None, x[1] if x[1] is not None else 0),
            reverse=reverse,
        )
    elif sort_by == "last_name":
        results.sort(key=lambda x: x[0].last_name.lower(), reverse=reverse)
    else:
        results.sort(key=lambda x: x[0].created_at, reverse=reverse)

    total = len(results)
    total_pages = math.ceil(total / per_page) if total > 0 else 0

    start = (page - 1) * per_page
    end = start + per_page
    page_results = results[start:end]

    items = [
        CandidateListItem(
            id=candidate.id,
            email=candidate.email,
            first_name=candidate.first_name,
            last_name=candidate.last_name,
            status=candidate.status,
            final_score=final_score,
            created_at=candidate.created_at,
        )
        for candidate, final_score in page_results
    ]

    return CandidateListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


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


def calculate_final_score(evaluations: list[Evaluation]) -> float | None:
    """
    Calculate the weighted final score from a list of evaluations.

    Returns None if fewer than 4 categories are evaluated (incomplete evaluation).
    Returns the weighted sum rounded to 2 decimals if all 4 categories are present.
    """
    if len(evaluations) < TOTAL_CATEGORIES:
        return None

    eval_by_category = {e.category: e.score for e in evaluations}

    if len(eval_by_category) < TOTAL_CATEGORIES:
        return None

    weighted_sum = 0.0
    for category, weight in CATEGORY_WEIGHTS.items():
        score = eval_by_category.get(category)
        if score is not None:
            weighted_sum += math.ceil(score * weight * 100) / 100

    return round(weighted_sum, 2)


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
