from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.university import University


def list_active_universities(db: Session) -> list[University]:
    return list(
        db.scalars(
            select(University)
            .where(University.active.is_(True))
            .order_by(University.name.asc())
        )
    )

