import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ConnectionStatus


def default_connection_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=7)


class Connection(Base):
    __tablename__ = "connections"
    __table_args__ = (
        UniqueConstraint("graduate_post_id", "student_id", name="uq_connection_post_student"),
        Index(
            "ix_connections_one_accepted_per_post",
            "graduate_post_id",
            unique=True,
            postgresql_where=text("status = 'accepted'"),
        ),
        Index(
            "ix_connections_student_pending_expiry",
            "student_id",
            "expires_at",
            postgresql_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graduate_post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("graduate_posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    graduate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("graduates.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=ConnectionStatus.PENDING.value)
    offered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=default_connection_expiry, nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    graduate_post = relationship("GraduatePost", back_populates="connections")
    graduate = relationship("Graduate", back_populates="connections")
    student = relationship("Student", back_populates="connections")

