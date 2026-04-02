from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.university import UniversityResponse
from app.services.university_service import list_active_universities


router = APIRouter(prefix="/api/universities", tags=["universities"])


@router.get("", response_model=list[UniversityResponse])
def list_universities(db: Session = Depends(get_db)) -> list[dict[str, str]]:
    universities = list_active_universities(db)
    return [
        {
            "id": str(university.id),
            "name": university.name,
            "slug": university.slug,
            "country": university.country,
        }
        for university in universities
    ]

