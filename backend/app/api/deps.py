from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.admin import Admin
from app.models.enums import StudentStatus, UserRole
from app.models.graduate import Graduate
from app.models.student import Student


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Graduate | Student | Admin:
    try:
        payload = decode_token(credentials.credentials)
        user_id = UUID(payload["sub"])
        role = payload["role"]
        token_type = payload["type"]
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.") from error

    if token_type != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.")

    model_map = {
        UserRole.GRADUATE.value: Graduate,
        UserRole.STUDENT.value: Student,
        UserRole.ADMIN.value: Admin,
    }
    model = model_map.get(role)
    if not model:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.")

    user = db.get(model, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not found.")

    return user


def get_current_graduate(current_user=Depends(get_current_user)) -> Graduate:
    if not isinstance(current_user, Graduate):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Graduate access required.")
    return current_user


def get_current_student(current_user=Depends(get_current_user)) -> Student:
    if not isinstance(current_user, Student):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access required.")
    if current_user.status != StudentStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is not active.")
    return current_user


def get_current_admin(current_user=Depends(get_current_user)) -> Admin:
    if not isinstance(current_user, Admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return current_user
