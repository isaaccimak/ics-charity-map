from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    AuthTokensResponse,
    GraduateRegisterRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    StudentRegisterRequest,
)
from app.services import auth_service


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register/graduate", response_model=MessageResponse, status_code=201)
def register_graduate(
    payload: GraduateRegisterRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return auth_service.register_graduate(db, payload)


@router.post("/register/student", response_model=MessageResponse, status_code=201)
def register_student(
    payload: StudentRegisterRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return auth_service.register_student(db, payload)


@router.post("/login", response_model=AuthTokensResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthTokensResponse:
    return auth_service.login(db, payload.email, payload.password)


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    return auth_service.refresh_tokens(db, payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    return auth_service.logout(db, payload.refresh_token)

