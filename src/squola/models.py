"""SQLAlchemy database models for Squola scheduling app."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    TypeDecorator,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class SchedulePreference(str, Enum):
    """Teacher scheduling preferences."""
    EARLY = "early"  # Prefer first hours
    LATE = "late"  # Prefer latest hours
    MINIMIZE_GAPS = "minimize_gaps"  # Group lessons together
    MAXIMIZE_GAPS = "maximize_gaps"  # More free time between lessons
    NONE = "none"  # No preference

class MatterRequirements(str, Enum):
    """Special requirements for subject matters."""
    AT_LEAST_TWICE_PER_WEEK = "at_least_twice_per_week"
    ONE_LESSON_OF_THREE_HOURS_PER_WEEK = "one_lesson_of_three_hours_per_week"
    ONE_LESSON_OF_TWO_HOURS_PER_WEEK = "one_lesson_of_two_hours_per_week"


class WorkspaceRole(str, Enum):
    """Role of a user in a workspace."""
    OWNER = "owner"
    MEMBER = "member"


class EnumArray(TypeDecorator):
    """
    Serialize/Deserialize a list of Enum values to/from a JSON column in SQLite.
    """
    impl = JSON

    def __init__(self, enum_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # Convert the list of Enum to a list of strings (enum values)
        return [e.value if isinstance(e, Enum) else e for e in value]

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Convert the list of strings back to Enum objects
        return [self.enum_class(v) for v in value]


# Association table for teacher-matter relationship (many-to-many)
teacher_matter_association = Table(
    "teacher_matter",
    Base.metadata,
    Column("teacher_id", Integer, ForeignKey("teachers.id"), primary_key=True),
    Column("matter_id", Integer, ForeignKey("matters.id"), primary_key=True),
)


class Workspace(Base):
    """Workspace model."""

    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    memberships: Mapped[list["WorkspaceMembership"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    teachers: Mapped[list["Teacher"]] = relationship(back_populates="workspace")
    classes: Mapped[list["SchoolClass"]] = relationship(back_populates="workspace")
    matters: Mapped[list["Matter"]] = relationship(back_populates="workspace")
    assignments: Mapped[list["ClassMatterAssignment"]] = relationship(back_populates="workspace")
    schedules: Mapped[list["SavedSchedule"]] = relationship(back_populates="workspace")


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    memberships: Mapped[list["WorkspaceMembership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    auth_sessions: Mapped[list["AuthSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class WorkspaceMembership(Base):
    """Membership between user and workspace."""

    __tablename__ = "workspace_memberships"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_membership"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default=WorkspaceRole.MEMBER.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workspace: Mapped["Workspace"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")


class AuthSession(Base):
    """Server-side persistent auth session."""

    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="auth_sessions")


class Teacher(Base):
    """Teacher model."""

    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    schedule_preference: Mapped[str] = mapped_column(String(50), default=SchedulePreference.NONE.value)

    workspace: Mapped["Workspace"] = relationship(back_populates="teachers")
    matters: Mapped[list["Matter"]] = relationship(
        secondary=teacher_matter_association,
        back_populates="teachers",
    )
    class_assignments: Mapped[list["ClassMatterAssignment"]] = relationship(
        back_populates="teacher",
    )
    unavailabilities: Mapped[list["TeacherUnavailability"]] = relationship(
        back_populates="teacher", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Teacher(id={self.id}, name='{self.first_name} {self.last_name}')"


class TeacherUnavailability(Base):
    """Represents time slots when a teacher is unavailable for scheduling."""

    __tablename__ = "teacher_unavailabilities"
    __table_args__ = (
        UniqueConstraint("teacher_id", "day_of_week", "hour_slot", name="uq_teacher_unavailability_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column()
    hour_slot: Mapped[int] = mapped_column()  # 1-based hour slot

    teacher: Mapped["Teacher"] = relationship(back_populates="unavailabilities")

    def __repr__(self) -> str:
        return f"TeacherUnavailability(teacher_id={self.teacher_id}, day={self.day_of_week}, slot={self.hour_slot})"


class SchoolClass(Base):
    """School class model."""

    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint("workspace_id", "year", "section", name="uq_workspace_class"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    year: Mapped[str] = mapped_column(String(10))  # Roman numeral: I, II, III, IV, V
    section: Mapped[str] = mapped_column(String(5))  # Letter: A, B, C, etc.

    workspace: Mapped["Workspace"] = relationship(back_populates="classes")
    matter_assignments: Mapped[list["ClassMatterAssignment"]] = relationship(
        back_populates="school_class",
        cascade="all, delete-orphan",
    )

    @property
    def name(self) -> str:
        """Returns the full class name (e.g., IIIA)."""
        return f"{self.year}{self.section}"

    def __repr__(self) -> str:
        return f"SchoolClass(id={self.id}, name='{self.name}')"


class Matter(Base):
    """Subject matter model."""

    __tablename__ = "matters"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_workspace_matter_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100))
    default_requirements: Mapped[list[MatterRequirements]] = mapped_column(
        EnumArray(MatterRequirements), nullable=True, default=list
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="matters")
    teachers: Mapped[list["Teacher"]] = relationship(
        secondary=teacher_matter_association,
        back_populates="matters",
    )
    class_assignments: Mapped[list["ClassMatterAssignment"]] = relationship(
        back_populates="matter",
    )

    def __repr__(self) -> str:
        return f"Matter(id={self.id}, name='{self.name}')"


class ClassMatterAssignment(Base):
    """Assignment of a teacher to a matter in a class."""

    __tablename__ = "class_matter_assignments"
    __table_args__ = (
        UniqueConstraint("class_id", "matter_id", name="uq_class_matter"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    matter_id: Mapped[int] = mapped_column(ForeignKey("matters.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False)
    hours_per_week: Mapped[int] = mapped_column()  # Fixed number of hours
    requirements: Mapped[list[MatterRequirements]] = mapped_column(EnumArray(MatterRequirements), nullable=True)

    workspace: Mapped["Workspace"] = relationship(back_populates="assignments")
    school_class: Mapped["SchoolClass"] = relationship(back_populates="matter_assignments")
    matter: Mapped["Matter"] = relationship(back_populates="class_assignments")
    teacher: Mapped["Teacher"] = relationship(back_populates="class_assignments")

    def __repr__(self) -> str:
        return f"ClassMatterAssignment(class_id={self.class_id}, matter_id={self.matter_id}, teacher_id={self.teacher_id})"


class SavedSchedule(Base):
    """A saved/generated schedule."""

    __tablename__ = "saved_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255))  # Auto-generated from datetime
    nickname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # User-friendly name
    status: Mapped[str] = mapped_column(String(50))  # OPTIMAL, FEASIBLE, etc.
    solve_time_seconds: Mapped[float] = mapped_column()
    total_slots: Mapped[int] = mapped_column()
    schedule_data: Mapped[str] = mapped_column(Text)  # JSON data
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="schedules")

    def __repr__(self) -> str:
        return f"SavedSchedule(id={self.id}, name='{self.name}', status='{self.status}')"
