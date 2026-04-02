import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PostStatus


def default_post_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=30)


class GraduatePost(Base):
    __tablename__ = "graduate_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graduate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("graduates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    university_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universities.id"),
        nullable=False,
        index=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=PostStatus.ACTIVE.value)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=default_post_expiry, nullable=False)
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    graduate = relationship("Graduate", back_populates="posts")
    university = relationship("University", back_populates="posts")
    connections = relationship("Connection", back_populates="graduate_post", cascade="all, delete-orphan")

