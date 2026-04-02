import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import GraduateStatus


class Graduate(Base):
    __tablename__ = "graduates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    degree_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    target_university_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("universities.id"),
        nullable=False,
        index=True,
    )
    gender: Mapped[str] = mapped_column(String(64), nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=False)
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=GraduateStatus.PENDING.value)
    rejection_note: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("admins.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    target_university = relationship("University", back_populates="graduates")
    preferences = relationship("GraduatePreference", back_populates="graduate", uselist=False, cascade="all, delete-orphan")
    posts = relationship("GraduatePost", back_populates="graduate", cascade="all, delete-orphan")
    connections = relationship("Connection", back_populates="graduate")


class GraduatePreference(Base):
    __tablename__ = "graduate_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graduate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("graduates.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    gender_pref: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False, default=list)
    year_of_study_min: Mapped[int | None] = mapped_column(Integer)
    year_of_study_max: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    graduate = relationship("Graduate", back_populates="preferences")

