"""SQLAlchemy database models for Squola scheduling app."""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, ForeignKey, String, Table, Column, Integer, Text, DateTime, TypeDecorator
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

# Association table for teacher-matter relationship (many-to-many)
teacher_matter_association = Table(
    "teacher_matter",
    Base.metadata,
    Column("teacher_id", Integer, ForeignKey("teachers.id"), primary_key=True),
    Column("matter_id", Integer, ForeignKey("matters.id"), primary_key=True),
)


class Teacher(Base):
    """
    Teacher model.
    
    A teacher can:
    - Teach one or more subject matters
    - Teach in one or more classes
    - Have blacklisted hours (if teaching at another school)
    - Express scheduling preferences
    """
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Scheduling preferences
    schedule_preference: Mapped[str] = mapped_column(
        String(50), default=SchedulePreference.NONE.value
    )
    
    # Relationships
    matters: Mapped[list["Matter"]] = relationship(
        secondary=teacher_matter_association,
        back_populates="teachers"
    )
    class_assignments: Mapped[list["ClassMatterAssignment"]] = relationship(
        back_populates="teacher"
    )
    blacklisted_slots: Mapped[list["TeacherBlacklistedSlot"]] = relationship(
        back_populates="teacher",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Teacher(id={self.id}, name='{self.first_name} {self.last_name}')"


class TeacherBlacklistedSlot(Base):
    """
    Represents time slots when a teacher is unavailable.
    Useful for teachers working in multiple schools.
    """
    __tablename__ = "teacher_blacklisted_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"))
    day_of_week: Mapped[int] = mapped_column() 
    hour_slot: Mapped[int] = mapped_column()  # 1-based hour slot

    teacher: Mapped["Teacher"] = relationship(back_populates="blacklisted_slots")

    def __repr__(self) -> str:
        return f"BlacklistedSlot(teacher_id={self.teacher_id}, day={self.day_of_week}, slot={self.hour_slot})"


class SchoolClass(Base):
    """
    School class model.
    
    A class is identified by a year (roman numeral) and a letter (e.g., IIIA, IIB).
    Each class has a list of subject matters with assigned teachers.
    """
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[str] = mapped_column(String(10))  # Roman numeral: I, II, III, IV, V
    section: Mapped[str] = mapped_column(String(5))  # Letter: A, B, C, etc.
    
    # Relationships
    matter_assignments: Mapped[list["ClassMatterAssignment"]] = relationship(
        back_populates="school_class",
        cascade="all, delete-orphan"
    )

    @property
    def name(self) -> str:
        """Returns the full class name (e.g., IIIA)."""
        return f"{self.year}{self.section}"

    def __repr__(self) -> str:
        return f"SchoolClass(id={self.id}, name='{self.name}')"


class Matter(Base):
    """
    Subject matter model.
    
    A subject matter (e.g., History, Geography, Maths) that can be taught
    by one or more teachers.
    """
    __tablename__ = "matters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    
    # Relationships
    teachers: Mapped[list["Teacher"]] = relationship(
        secondary=teacher_matter_association,
        back_populates="matters"
    )
    class_assignments: Mapped[list["ClassMatterAssignment"]] = relationship(
        back_populates="matter"
    )

    def __repr__(self) -> str:
        return f"Matter(id={self.id}, name='{self.name}')"

class EnumArray(TypeDecorator):
    """
    Serializza/Deserializza una lista di Enum in una colonna JSON di SQLite.
    """
    impl = JSON

    def __init__(self, enum_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # Converte la lista di Enum in una lista di stringhe (i valori dell'enum)
        return [e.value if isinstance(e, Enum) else e for e in value]

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Riconverte la lista di stringhe in oggetti Enum
        return [self.enum_class(v) for v in value]

class ClassMatterAssignment(Base):
    """
    Assignment of a specific teacher to teach a specific matter in a specific class.
    
    This enforces the rule that a class has a single teacher teaching each subject matter.
    Also stores the hours per week for that matter in that class.
    """
    __tablename__ = "class_matter_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"))
    matter_id: Mapped[int] = mapped_column(ForeignKey("matters.id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"))
    hours_per_week: Mapped[int] = mapped_column()  # Fixed number of hours
    requirements: Mapped[list[MatterRequirements]] = mapped_column(EnumArray(MatterRequirements), nullable=True)

    # Relationships
    school_class: Mapped["SchoolClass"] = relationship(back_populates="matter_assignments")
    matter: Mapped["Matter"] = relationship(back_populates="class_assignments")
    teacher: Mapped["Teacher"] = relationship(back_populates="class_assignments")

    def __repr__(self) -> str:
        return f"ClassMatterAssignment(class_id={self.class_id}, matter_id={self.matter_id}, teacher_id={self.teacher_id})"


class SavedSchedule(Base):
    """
    A saved/generated schedule.
    
    Stores the full schedule data as JSON along with metadata about
    when it was generated and its status.
    """
    __tablename__ = "saved_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))  # Auto-generated from datetime
    nickname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # User-friendly name
    status: Mapped[str] = mapped_column(String(50))  # OPTIMAL, FEASIBLE, etc.
    solve_time_seconds: Mapped[float] = mapped_column()
    total_slots: Mapped[int] = mapped_column()
    schedule_data: Mapped[str] = mapped_column(Text)  # JSON data
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"SavedSchedule(id={self.id}, name='{self.name}', status='{self.status}')"
