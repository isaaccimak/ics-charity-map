from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import GraduateStatus, StudentStatus
from app.models.graduate import Graduate
from app.models.student import Student


def list_pending_graduates(db: Session) -> list[Graduate]:
    return list(
        db.scalars(
            select(Graduate)
            .where(Graduate.status == GraduateStatus.PENDING.value)
            .options(selectinload(Graduate.target_university))
            .order_by(Graduate.submitted_at.asc())
        )
    )


def decide_graduate(
    db: Session,
    graduate_id: UUID,
    admin_id: UUID,
    decision: str,
    note: str | None,
) -> dict[str, str]:
    graduate = db.get(Graduate, graduate_id)
    if not graduate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graduate not found.")
    if decision == GraduateStatus.REJECTED.value and not note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rejection note is required.")

    graduate.status = decision
    graduate.rejection_note = note.strip() if decision == GraduateStatus.REJECTED.value and note else None
    graduate.reviewed_at = datetime.now(UTC)
    graduate.reviewed_by = admin_id
    db.commit()
    return {"message": f"Graduate {decision}."}


def list_pending_students(db: Session) -> list[Student]:
    return list(
        db.scalars(
            select(Student)
            .where(Student.status == StudentStatus.PENDING.value)
            .options(selectinload(Student.university))
            .order_by(Student.created_at.asc())
        )
    )


def activate_student(db: Session, student_id: UUID) -> dict[str, str]:
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    student.status = StudentStatus.ACTIVE.value
    student.activated_at = datetime.now(UTC)
    db.commit()
    return {"message": "Student activated."}

