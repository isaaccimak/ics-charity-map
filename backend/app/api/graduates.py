from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_graduate
from app.core.database import get_db
from app.models.graduate import Graduate
from app.schemas.auth import MessageResponse
from app.schemas.graduate import (
    GraduateMeResponse,
    GraduatePostCreateRequest,
    GraduatePostResponse,
    GraduatePreferenceRequest,
    GraduatePreferenceResponse,
    GraduateProfileUpdateRequest,
)
from app.services import graduate_service


router = APIRouter(prefix="/api/graduates", tags=["graduates"])


def _serialize_preferences(graduate: Graduate) -> dict[str, object]:
    if not graduate.preferences:
        return {
            "gender_pref": [],
            "year_of_study_min": None,
            "year_of_study_max": None,
        }
    return {
        "gender_pref": graduate.preferences.gender_pref,
        "year_of_study_min": graduate.preferences.year_of_study_min,
        "year_of_study_max": graduate.preferences.year_of_study_max,
    }


@router.get("/me", response_model=GraduateMeResponse)
def get_me(
    current_graduate: Graduate = Depends(get_current_graduate),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    graduate = graduate_service.get_graduate(db, current_graduate.id)
    return {
        "id": str(graduate.id),
        "email": graduate.email,
        "full_name": graduate.full_name,
        "graduation_year": graduate.graduation_year,
        "degree_subject": graduate.degree_subject,
        "target_university_id": str(graduate.target_university_id),
        "gender": graduate.gender,
        "bio": graduate.bio,
        "linkedin_url": graduate.linkedin_url,
        "status": graduate.status,
        "rejection_note": graduate.rejection_note,
        "submitted_at": graduate.submitted_at,
        "reviewed_at": graduate.reviewed_at,
        "preferences": _serialize_preferences(graduate),
    }


@router.patch("/me/profile", response_model=GraduateMeResponse)
def update_profile(
    payload: GraduateProfileUpdateRequest,
    current_graduate: Graduate = Depends(get_current_graduate),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    graduate = graduate_service.update_profile(db, current_graduate.id, payload)
    return {
        "id": str(graduate.id),
        "email": graduate.email,
        "full_name": graduate.full_name,
        "graduation_year": graduate.graduation_year,
        "degree_subject": graduate.degree_subject,
        "target_university_id": str(graduate.target_university_id),
        "gender": graduate.gender,
        "bio": graduate.bio,
        "linkedin_url": graduate.linkedin_url,
        "status": graduate.status,
        "rejection_note": graduate.rejection_note,
        "submitted_at": graduate.submitted_at,
        "reviewed_at": graduate.reviewed_at,
        "preferences": _serialize_preferences(graduate),
    }


@router.put("/me/preferences", response_model=GraduatePreferenceResponse)
def set_preferences(
    payload: GraduatePreferenceRequest,
    current_graduate: Graduate = Depends(get_current_graduate),
    db: Session = Depends(get_db),
):
    return graduate_service.save_preferences(db, current_graduate.id, payload)


@router.post("/me/posts", response_model=MessageResponse, status_code=201)
def publish_post(
    payload: GraduatePostCreateRequest,
    current_graduate: Graduate = Depends(get_current_graduate),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    graduate_service.publish_post(db, current_graduate.id, payload)
    return {"message": "Post published."}


@router.get("/me/posts", response_model=list[GraduatePostResponse])
def list_posts(
    current_graduate: Graduate = Depends(get_current_graduate),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    posts = graduate_service.list_posts(db, current_graduate.id)
    return [
        {
            "id": str(post.id),
            "university_id": str(post.university_id),
            "university_name": post.university.name if post.university else "Unknown university",
            "message": post.message,
            "status": post.status,
            "published_at": post.published_at,
            "expires_at": post.expires_at,
            "matched_at": post.matched_at,
            "connections": [
                {
                    "id": str(connection.id),
                    "student_id": str(connection.student_id),
                    "status": connection.status,
                    "offered_at": connection.offered_at,
                    "expires_at": connection.expires_at,
                    "responded_at": connection.responded_at,
                }
                for connection in post.connections
            ],
        }
        for post in posts
    ]


@router.delete("/me/posts/{post_id}", response_model=MessageResponse)
def withdraw_post(
    post_id: UUID,
    current_graduate: Graduate = Depends(get_current_graduate),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return graduate_service.withdraw_post(db, current_graduate.id, post_id)

