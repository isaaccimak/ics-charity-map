from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GraduatePreferenceRequest(BaseModel):
    gender_pref: list[str] = Field(default_factory=list)
    year_of_study_min: int | None = Field(default=None, ge=1, le=6)
    year_of_study_max: int | None = Field(default=None, ge=1, le=6)


class GraduateProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    bio: str | None = Field(default=None, min_length=1, max_length=300)
    linkedin_url: str | None = Field(default=None, max_length=500)


class GraduatePostCreateRequest(BaseModel):
    university_id: UUID
    message: str = Field(min_length=1, max_length=500)


class GraduatePreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    gender_pref: list[str]
    year_of_study_min: int | None
    year_of_study_max: int | None


class GraduateMeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    graduation_year: int
    degree_subject: str
    target_university_id: str
    gender: str
    bio: str
    linkedin_url: str | None
    status: str
    rejection_note: str | None
    submitted_at: datetime
    reviewed_at: datetime | None
    preferences: GraduatePreferenceResponse


class GraduateConnectionSummary(BaseModel):
    id: str
    student_id: str
    status: str
    offered_at: datetime
    expires_at: datetime
    responded_at: datetime | None


class GraduatePostResponse(BaseModel):
    id: str
    university_id: str
    university_name: str
    message: str
    status: str
    published_at: datetime
    expires_at: datetime
    matched_at: datetime | None
    connections: list[GraduateConnectionSummary]
