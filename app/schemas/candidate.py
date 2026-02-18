from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.candidate import CandidateStatus


class CandidateCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    status: CandidateStatus = CandidateStatus.applied


class CandidateUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = Field(default=None, min_length=1)
    last_name: str | None = Field(default=None, min_length=1)
    status: CandidateStatus | None = None


class CandidateResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    status: CandidateStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CandidateListItem(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    status: CandidateStatus
    final_score: float | None
    created_at: datetime


class CandidateListResponse(BaseModel):
    items: list[CandidateListItem]
    total: int
    page: int
    per_page: int
    total_pages: int
