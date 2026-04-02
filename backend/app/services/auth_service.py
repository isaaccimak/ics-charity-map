from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.admin import Admin
from app.models.enums import GraduateStatus, StudentStatus, UserRole
from app.models.graduate import Graduate
from app.models.refresh_token import RefreshToken
from app.models.student import Student
from app.models.university import University
from app.schemas.auth import AuthTokensResponse, AuthUserResponse, GraduateRegisterRequest, StudentRegisterRequest


ROLE_MODEL_MAP = {
    UserRole.GRADUATE.value: Graduate,
    UserRole.STUDENT.value: Student,
    UserRole.ADMIN.value: Admin,
}


def _hash_refresh_token(refresh_token: str) -> str:
    return sha256(refresh_token.encode("utf-8")).hexdigest()


def _ensure_email_available(db: Session, email: str) -> None:
    normalized_email = email.strip().lower()
    for model in (Graduate, Student, Admin):
        existing = db.scalar(select(model.id).where(model.email == normalized_email))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )


def _duplicate_email_error(error: IntegrityError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="An account with this email already exists.",
    )


def _issue_token_pair(db: Session, user_id: UUID, email: str, role: str) -> tuple[str, str]:
    access_token = create_access_token(user_id=user_id, email=email, role=role)
    refresh_token = create_refresh_token(user_id=user_id, role=role)
    db.add(
        RefreshToken(
            user_id=user_id,
            user_role=role,
            token_hash=_hash_refresh_token(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days),
        )
    )
    return access_token, refresh_token


def register_graduate(db: Session, payload: GraduateRegisterRequest) -> dict[str, str]:
    normalized_email = payload.email.strip().lower()

    existing_graduate = db.scalar(select(Graduate).where(Graduate.email == normalized_email))
    if existing_graduate:
        if existing_graduate.status != GraduateStatus.REJECTED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )
        if (
            existing_graduate.reviewed_at is None
            or existing_graduate.reviewed_at > datetime.now(UTC) - timedelta(days=7)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Please wait 7 days after rejection before reapplying.",
            )

    for model in (Student, Admin):
        existing = db.scalar(select(model.id).where(model.email == normalized_email))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

    university = db.get(University, payload.target_university_id)
    if not university or not university.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found.")

    if existing_graduate:
        existing_graduate.password_hash = hash_password(payload.password)
        existing_graduate.full_name = payload.full_name.strip()
        existing_graduate.graduation_year = payload.graduation_year
        existing_graduate.degree_subject = payload.degree_subject.strip()
        existing_graduate.target_university_id = payload.target_university_id
        existing_graduate.gender = payload.gender
        existing_graduate.bio = payload.bio.strip()
        existing_graduate.linkedin_url = payload.linkedin_url.strip() if payload.linkedin_url else None
        existing_graduate.status = GraduateStatus.PENDING.value
        existing_graduate.rejection_note = None
        existing_graduate.submitted_at = datetime.now(UTC)
        existing_graduate.reviewed_at = None
        existing_graduate.reviewed_by = None
    else:
        db.add(
            Graduate(
                email=normalized_email,
                password_hash=hash_password(payload.password),
                full_name=payload.full_name.strip(),
                graduation_year=payload.graduation_year,
                degree_subject=payload.degree_subject.strip(),
                target_university_id=payload.target_university_id,
                gender=payload.gender,
                bio=payload.bio.strip(),
                linkedin_url=payload.linkedin_url.strip() if payload.linkedin_url else None,
                status=GraduateStatus.PENDING.value,
            )
        )

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise _duplicate_email_error(error) from error

    return {"message": "Application submitted. You will be notified once an admin reviews it."}


def register_student(db: Session, payload: StudentRegisterRequest) -> dict[str, str]:
    _ensure_email_available(db, payload.email)
    university = db.get(University, payload.university_id)
    if not university or not university.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found.")

    student = Student(
        email=payload.email.strip().lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        university_id=payload.university_id,
        year_of_study=payload.year_of_study,
        gender=payload.gender,
        status=StudentStatus.PENDING.value,
    )
    db.add(student)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise _duplicate_email_error(error) from error

    return {"message": "Registration submitted. Your account is awaiting admin activation."}


def _check_user_status(user: Graduate | Student | Admin, role: str) -> None:
    if role == UserRole.STUDENT.value:
        student = user
        if student.status != StudentStatus.ACTIVE.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is not yet active.")


def login(db: Session, email: str, password: str) -> AuthTokensResponse:
    normalized_email = email.strip().lower()

    for role, model in ROLE_MODEL_MAP.items():
        user = db.scalar(select(model).where(model.email == normalized_email))
        if not user:
            continue
        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        _check_user_status(user, role)
        access_token, refresh_token = _issue_token_pair(db, user.id, user.email, role)
        db.commit()

        return AuthTokensResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=AuthUserResponse(
                id=str(user.id),
                email=user.email,
                role=role,
                full_name=user.full_name,
            ),
        )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")


def refresh_tokens(db: Session, refresh_token: str) -> dict[str, str]:
    try:
        payload = decode_token(refresh_token)
        user_id = UUID(payload["sub"])
        role = payload["role"]
        token_type = payload["type"]
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.") from error

    if token_type != "refresh" or role not in ROLE_MODEL_MAP:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    stored_token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.token_hash == _hash_refresh_token(refresh_token),
        )
    )
    if not stored_token or stored_token.revoked_at or stored_token.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked.")

    model = ROLE_MODEL_MAP[role]
    user = db.get(model, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account no longer exists.")

    _check_user_status(user, role)

    stored_token.revoked_at = datetime.now(UTC)
    access_token, new_refresh_token = _issue_token_pair(db, user.id, user.email, role)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
    }


def logout(db: Session, refresh_token: str) -> dict[str, str]:
    token_hash = _hash_refresh_token(refresh_token)
    stored_token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if stored_token and not stored_token.revoked_at:
        stored_token.revoked_at = datetime.now(UTC)
        db.commit()
    return {"message": "Logged out successfully."}
