"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-03
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admins_email"), "admins", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_role", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)

    op.create_table(
        "universities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_universities_slug"), "universities", ["slug"], unique=True)

    op.create_table(
        "graduates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("graduation_year", sa.Integer(), nullable=False),
        sa.Column("degree_subject", sa.String(length=255), nullable=False),
        sa.Column("target_university_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gender", sa.String(length=64), nullable=False),
        sa.Column("bio", sa.Text(), nullable=False),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("rejection_note", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["reviewed_by"], ["admins.id"]),
        sa.ForeignKeyConstraint(["target_university_id"], ["universities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_graduates_email"), "graduates", ["email"], unique=True)
    op.create_index(op.f("ix_graduates_target_university_id"), "graduates", ["target_university_id"], unique=False)

    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("university_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("year_of_study", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_students_email"), "students", ["email"], unique=True)
    op.create_index(op.f("ix_students_university_id"), "students", ["university_id"], unique=False)

    op.create_table(
        "graduate_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("graduate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gender_pref", postgresql.ARRAY(sa.String(length=64)), nullable=False),
        sa.Column("year_of_study_min", sa.Integer(), nullable=True),
        sa.Column("year_of_study_max", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["graduate_id"], ["graduates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_graduate_preferences_graduate_id"), "graduate_preferences", ["graduate_id"], unique=True)

    op.create_table(
        "graduate_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("graduate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("university_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["graduate_id"], ["graduates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_graduate_posts_graduate_id"), "graduate_posts", ["graduate_id"], unique=False)
    op.create_index(op.f("ix_graduate_posts_university_id"), "graduate_posts", ["university_id"], unique=False)

    op.create_table(
        "connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("graduate_post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("graduate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("offered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["graduate_id"], ["graduates.id"]),
        sa.ForeignKeyConstraint(["graduate_post_id"], ["graduate_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("graduate_post_id", "student_id", name="uq_connection_post_student"),
    )
    op.create_index(
        "ix_connections_one_accepted_per_post",
        "connections",
        ["graduate_post_id"],
        unique=True,
        postgresql_where=sa.text("status = 'accepted'"),
    )
    op.create_index(
        "ix_connections_student_pending_expiry",
        "connections",
        ["student_id", "expires_at"],
        unique=False,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index("ix_connections_student_pending_expiry", table_name="connections", postgresql_where=sa.text("status = 'pending'"))
    op.drop_index("ix_connections_one_accepted_per_post", table_name="connections", postgresql_where=sa.text("status = 'accepted'"))
    op.drop_table("connections")
    op.drop_index(op.f("ix_graduate_posts_university_id"), table_name="graduate_posts")
    op.drop_index(op.f("ix_graduate_posts_graduate_id"), table_name="graduate_posts")
    op.drop_table("graduate_posts")
    op.drop_index(op.f("ix_graduate_preferences_graduate_id"), table_name="graduate_preferences")
    op.drop_table("graduate_preferences")
    op.drop_index(op.f("ix_students_university_id"), table_name="students")
    op.drop_index(op.f("ix_students_email"), table_name="students")
    op.drop_table("students")
    op.drop_index(op.f("ix_graduates_target_university_id"), table_name="graduates")
    op.drop_index(op.f("ix_graduates_email"), table_name="graduates")
    op.drop_table("graduates")
    op.drop_index(op.f("ix_universities_slug"), table_name="universities")
    op.drop_table("universities")
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index(op.f("ix_admins_email"), table_name="admins")
    op.drop_table("admins")
