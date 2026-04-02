from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_student
from app.core.database import get_db
from app.models.student import Student
from app.schemas.auth import MessageResponse
from app.schemas.student import StudentFeedResponse
from app.services import student_service


router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("/me/feed", response_model=StudentFeedResponse)
def get_feed(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    items, total = student_service.list_feed(db, current_student.id, page, limit)
    return {
        "items": [
            {
                "id": str(connection.id),
                "offered_at": connection.offered_at,
                "expires_at": connection.expires_at,
                "post": {
                    "id": str(connection.graduate_post.id),
                    "message": connection.graduate_post.message,
                    "published_at": connection.graduate_post.published_at,
                    "university_name": connection.graduate_post.university.name,
                },
                "graduate": {
                    "id": str(connection.graduate.id),
                    "full_name": connection.graduate.full_name,
                    "graduation_year": connection.graduate.graduation_year,
                    "degree_subject": connection.graduate.degree_subject,
                    "bio": connection.graduate.bio,
                },
            }
            for connection in items
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("/me/connections/{connection_id}/accept", response_model=MessageResponse)
def accept_connection(
    connection_id: UUID,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return student_service.accept_connection(db, current_student.id, connection_id)


@router.post("/me/connections/{connection_id}/decline", response_model=MessageResponse)
def decline_connection(
    connection_id: UUID,
    current_student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return student_service.decline_connection(db, current_student.id, connection_id)
