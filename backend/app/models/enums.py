from enum import StrEnum


class UserRole(StrEnum):
    GRADUATE = "graduate"
    STUDENT = "student"
    ADMIN = "admin"


class GraduateStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class StudentStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class PostStatus(StrEnum):
    ACTIVE = "active"
    MATCHED = "matched"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class ConnectionStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"

