from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.connection import Connection
from app.models.enums import ConnectionStatus, GraduateStatus, PostStatus
from app.models.graduate import Graduate, GraduatePreference
from app.models.graduate_post import GraduatePost
from app.models.student import Student
from app.models.university import University
from app.schemas.graduate import GraduatePostCreateRequest, GraduatePreferenceRequest, GraduateProfileUpdateRequest


def get_graduate(db: Session, graduate_id: UUID) -> Graduate:
    graduate = db.scalar(
        select(Graduate)
        .where(Graduate.id == graduate_id)
        .options(selectinload(Graduate.preferences))
    )
    if not graduate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graduate not found.")
    return graduate


def update_profile(db: Session, graduate_id: UUID, payload: GraduateProfileUpdateRequest) -> Graduate:
    graduate = get_graduate(db, graduate_id)
    if payload.full_name is not None:
        graduate.full_name = payload.full_name.strip()
    if payload.bio is not None:
        graduate.bio = payload.bio.strip()
    if payload.linkedin_url is not None:
        graduate.linkedin_url = payload.linkedin_url.strip() if payload.linkedin_url.strip() else None
    db.commit()
    db.refresh(graduate)
    return get_graduate(db, graduate_id)


def save_preferences(db: Session, graduate_id: UUID, payload: GraduatePreferenceRequest) -> GraduatePreference:
    if (
        payload.year_of_study_min is not None
        and payload.year_of_study_max is not None
        and payload.year_of_study_min > payload.year_of_study_max
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="year_of_study_min cannot be greater than year_of_study_max.",
        )

    graduate = get_graduate(db, graduate_id)
    if graduate.status != GraduateStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account must be approved before setting preferences.",
        )

    if graduate.preferences:
        prefs = graduate.preferences
        prefs.gender_pref = payload.gender_pref
        prefs.year_of_study_min = payload.year_of_study_min
        prefs.year_of_study_max = payload.year_of_study_max
        prefs.updated_at = datetime.now(UTC)
    else:
        prefs = GraduatePreference(
            graduate_id=graduate_id,
            gender_pref=payload.gender_pref,
            year_of_study_min=payload.year_of_study_min,
            year_of_study_max=payload.year_of_study_max,
        )
        db.add(prefs)

    db.commit()
    db.refresh(prefs)
    return prefs


def _matching_students_query(graduate: Graduate, university_id: UUID):
    query = select(Student).where(
        Student.university_id == university_id,
        Student.status == "active",
    )

    prefs = graduate.preferences
    if prefs and prefs.gender_pref:
        query = query.where(Student.gender.in_(prefs.gender_pref))
    if prefs and prefs.year_of_study_min is not None:
        query = query.where(Student.year_of_study >= prefs.year_of_study_min)
    if prefs and prefs.year_of_study_max is not None:
        query = query.where(Student.year_of_study <= prefs.year_of_study_max)

    return query


def publish_post(db: Session, graduate_id: UUID, payload: GraduatePostCreateRequest) -> GraduatePost:
    graduate = get_graduate(db, graduate_id)
    if graduate.status != GraduateStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account must be approved before publishing posts.",
        )

    university_id = payload.university_id
    university = db.get(University, university_id)
    if not university or not university.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="University not found.")

    post = GraduatePost(
        graduate_id=graduate_id,
        university_id=university_id,
        message=payload.message.strip(),
        status=PostStatus.ACTIVE.value,
    )
    db.add(post)
    db.flush()

    for student in db.scalars(_matching_students_query(graduate, university_id)):
        db.add(
            Connection(
                graduate_post_id=post.id,
                graduate_id=graduate_id,
                student_id=student.id,
                status=ConnectionStatus.PENDING.value,
            )
        )

    db.commit()
    db.refresh(post)
    return post


def list_posts(db: Session, graduate_id: UUID) -> list[GraduatePost]:
    return list(
        db.scalars(
            select(GraduatePost)
            .where(GraduatePost.graduate_id == graduate_id)
            .options(
                selectinload(GraduatePost.university),
                selectinload(GraduatePost.connections),
            )
            .order_by(GraduatePost.published_at.desc())
        )
    )


def withdraw_post(db: Session, graduate_id: UUID, post_id: UUID) -> dict[str, str]:
    post = db.scalar(
        select(GraduatePost)
        .where(
            GraduatePost.id == post_id,
            GraduatePost.graduate_id == graduate_id,
        )
        .options(selectinload(GraduatePost.connections))
    )
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    if post.status == PostStatus.MATCHED.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot withdraw a matched post.")

    post.status = PostStatus.WITHDRAWN.value
    for connection in post.connections:
        if connection.status == ConnectionStatus.PENDING.value:
            connection.status = ConnectionStatus.EXPIRED.value

    db.commit()
    return {"message": "Post withdrawn."}
