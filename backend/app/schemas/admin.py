from datetime import datetime

from pydantic import BaseModel, Field


class GraduateDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    note: str | None = Field(default=None, max_length=1000)


class PendingGraduateResponse(BaseModel):
    id: str
    email: str
    full_name: str
    graduation_year: int
    degree_subject: str
    target_university_id: str
    target_university_name: str
    gender: str
    bio: str
    linkedin_url: str | None
    submitted_at: datetime


class PendingStudentResponse(BaseModel):
    id: str
    email: str
    full_name: str
    university_id: str
    university_name: str
    year_of_study: int
    gender: str
    created_at: datetime

