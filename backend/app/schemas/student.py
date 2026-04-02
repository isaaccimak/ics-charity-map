from datetime import datetime

from pydantic import BaseModel


class FeedGraduateResponse(BaseModel):
    id: str
    full_name: str
    graduation_year: int
    degree_subject: str
    bio: str


class FeedPostResponse(BaseModel):
    id: str
    message: str
    published_at: datetime
    university_name: str


class FeedItemResponse(BaseModel):
    id: str
    offered_at: datetime
    expires_at: datetime
    post: FeedPostResponse
    graduate: FeedGraduateResponse


class StudentFeedResponse(BaseModel):
    items: list[FeedItemResponse]
    total: int
    page: int
    limit: int
