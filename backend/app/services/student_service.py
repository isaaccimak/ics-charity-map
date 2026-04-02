from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.connection import Connection
from app.models.enums import ConnectionStatus, PostStatus
from app.models.graduate_post import GraduatePost


def list_feed(db: Session, student_id: UUID, page: int, limit: int) -> tuple[list[Connection], int]:
    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    now = datetime.now(UTC)

    total = db.scalar(
        select(func.count())
        .select_from(Connection)
        .where(
            Connection.student_id == student_id,
            Connection.status == ConnectionStatus.PENDING.value,
            Connection.expires_at > now,
        )
    ) or 0

    items = list(
        db.scalars(
            select(Connection)
            .where(
                Connection.student_id == student_id,
                Connection.status == ConnectionStatus.PENDING.value,
                Connection.expires_at > now,
            )
            .options(
                selectinload(Connection.graduate_post).selectinload(GraduatePost.university),
                selectinload(Connection.graduate),
            )
            .order_by(Connection.offered_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    )

    return items, total


def _get_owned_pending_connection(db: Session, student_id: UUID, connection_id: UUID) -> Connection:
    connection = db.scalar(
        select(Connection)
        .where(Connection.id == connection_id)
        .options(selectinload(Connection.graduate_post))
    )
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found.")
    if connection.student_id != student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your connection.")
    if connection.status != ConnectionStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Connection is already {connection.status}.",
        )
    if connection.expires_at <= datetime.now(UTC):
        connection.status = ConnectionStatus.EXPIRED.value
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Connection offer has expired.")
    return connection


def accept_connection(db: Session, student_id: UUID, connection_id: UUID) -> dict[str, str]:
    connection = _get_owned_pending_connection(db, student_id, connection_id)
    post = connection.graduate_post
    if post.status != PostStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This post is no longer available.")

    now = datetime.now(UTC)
    connection.status = ConnectionStatus.ACCEPTED.value
    connection.responded_at = now
    post.status = PostStatus.MATCHED.value
    post.matched_at = now

    for other in db.scalars(
        select(Connection).where(
            Connection.graduate_post_id == post.id,
            Connection.id != connection.id,
            Connection.status == ConnectionStatus.PENDING.value,
        )
    ):
        other.status = ConnectionStatus.EXPIRED.value

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This post has already been accepted by another student.",
        ) from error
    return {"message": "Connection accepted."}


def decline_connection(db: Session, student_id: UUID, connection_id: UUID) -> dict[str, str]:
    connection = _get_owned_pending_connection(db, student_id, connection_id)
    connection.status = ConnectionStatus.DECLINED.value
    connection.responded_at = datetime.now(UTC)
    db.commit()
    return {"message": "Connection declined."}
