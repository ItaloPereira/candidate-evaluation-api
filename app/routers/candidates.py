from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.evaluation import Evaluation
from app.schemas.candidate import CandidateCreate, CandidateResponse, CandidateUpdate
from app.schemas.evaluation import EvaluationCreate, EvaluationResponse

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
