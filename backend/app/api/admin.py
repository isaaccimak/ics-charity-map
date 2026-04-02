from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.admin import Admin
from app.schemas.admin import GraduateDecisionRequest, PendingGraduateResponse, PendingStudentResponse
from app.schemas.auth import MessageResponse
from app.services import admin_service


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/graduates/pending", response_model=list[PendingGraduateResponse])
def list_pending_graduates(
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    graduates = admin_service.list_pending_graduates(db)
    return [
        {
            "id": str(graduate.id),
            "email": graduate.email,
            "full_name": graduate.full_name,
            "graduation_year": graduate.graduation_year,
            "degree_subject": graduate.degree_subject,
            "target_university_id": str(graduate.target_university_id),
            "target_university_name": graduate.target_university.name,
            "gender": graduate.gender,
            "bio": graduate.bio,
            "linkedin_url": graduate.linkedin_url,
            "submitted_at": graduate.submitted_at,
        }
        for graduate in graduates
    ]


@router.patch("/graduates/{graduate_id}/decision", response_model=MessageResponse)
def decide_graduate(
    graduate_id: UUID,
    payload: GraduateDecisionRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return admin_service.decide_graduate(
        db=db,
        graduate_id=graduate_id,
        admin_id=current_admin.id,
        decision=payload.decision,
        note=payload.note,
    )


@router.get("/students/pending", response_model=list[PendingStudentResponse])
def list_pending_students(
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    students = admin_service.list_pending_students(db)
    return [
        {
            "id": str(student.id),
            "email": student.email,
            "full_name": student.full_name,
            "university_id": str(student.university_id),
            "university_name": student.university.name,
            "year_of_study": student.year_of_study,
            "gender": student.gender,
            "created_at": student.created_at,
        }
        for student in students
    ]


@router.patch("/students/{student_id}/activate", response_model=MessageResponse)
def activate_student(
    student_id: UUID,
    _: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return admin_service.activate_student(db, student_id)

