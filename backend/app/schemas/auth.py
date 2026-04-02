from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class GraduateRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    graduation_year: int = Field(ge=1990, le=2100)
    degree_subject: str = Field(min_length=1, max_length=255)
    target_university_id: UUID
    gender: str = Field(min_length=1, max_length=64)
    bio: str = Field(min_length=1, max_length=300)
    linkedin_url: str | None = Field(default=None, max_length=500)


class StudentRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    university_id: UUID
    year_of_study: int = Field(ge=1, le=6)
    gender: str = Field(min_length=1, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class AuthUserResponse(BaseModel):
    id: str
    email: EmailStr
    role: str
    full_name: str


class AuthTokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: AuthUserResponse


class MessageResponse(BaseModel):
    message: str
