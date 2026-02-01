"""Pydantic schemas for API request/response validation."""

from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class SchedulePreference(str, Enum):
    """Teacher scheduling preferences."""
    EARLY = "early"
    LATE = "late"
    MINIMIZE_GAPS = "minimize_gaps"
    MAXIMIZE_GAPS = "maximize_gaps"
    NONE = "none"


# ============ Blacklisted Slot Schemas ============

class BlacklistedSlotBase(BaseModel):
    """Base schema for blacklisted time slots."""
    day_of_week: int = Field(..., ge=0, le=4, description="Day of week (0=Monday, 4=Friday)")
    hour_slot: int = Field(..., ge=1, description="Hour slot (1-based)")


class BlacklistedSlotCreate(BlacklistedSlotBase):
    """Schema for creating a blacklisted slot."""
    pass


class BlacklistedSlotResponse(BlacklistedSlotBase):
    """Schema for blacklisted slot response."""
    id: int

    model_config = {"from_attributes": True}


# ============ Matter Schemas ============

class MatterBase(BaseModel):
    """Base schema for subject matters."""
    name: str = Field(..., min_length=1, max_length=100)


class MatterCreate(MatterBase):
    """Schema for creating a matter."""
    pass


class MatterUpdate(BaseModel):
    """Schema for updating a matter."""
    name: str | None = Field(None, min_length=1, max_length=100)


class MatterResponse(MatterBase):
    """Schema for matter response."""
    id: int

    model_config = {"from_attributes": True}


class MatterWithTeachersResponse(MatterResponse):
    """Schema for matter response including teachers."""
    teachers: list["TeacherResponse"] = []

    model_config = {"from_attributes": True}


# ============ Teacher Schemas ============

class TeacherBase(BaseModel):
    """Base schema for teachers."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str | None = Field(None, max_length=255)
    schedule_preference: SchedulePreference = SchedulePreference.NONE


class TeacherCreate(TeacherBase):
    """Schema for creating a teacher."""
    matter_ids: list[int] = Field(default_factory=list, description="IDs of matters this teacher can teach")


class TeacherUpdate(BaseModel):
    """Schema for updating a teacher."""
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: str | None = Field(None, max_length=255)
    schedule_preference: SchedulePreference | None = None
    matter_ids: list[int] | None = Field(None, description="IDs of matters this teacher can teach")


class TeacherResponse(TeacherBase):
    """Schema for teacher response."""
    id: int

    model_config = {"from_attributes": True}


class TeacherWithMattersResponse(TeacherResponse):
    """Schema for teacher response including matters."""
    matters: list[MatterResponse] = []
    blacklisted_slots: list[BlacklistedSlotResponse] = []

    model_config = {"from_attributes": True}


# ============ School Class Schemas ============

class SchoolClassBase(BaseModel):
    """Base schema for school classes."""
    year: str = Field(..., min_length=1, max_length=10, description="Year in Roman numerals (I, II, III, IV, V)")
    section: str = Field(..., min_length=1, max_length=5, description="Section letter (A, B, C, etc.)")


class SchoolClassCreate(SchoolClassBase):
    """Schema for creating a school class."""
    pass


class SchoolClassUpdate(BaseModel):
    """Schema for updating a school class."""
    year: str | None = Field(None, min_length=1, max_length=10)
    section: str | None = Field(None, min_length=1, max_length=5)


class SchoolClassResponse(SchoolClassBase):
    """Schema for school class response."""
    id: int
    name: str = Field(..., description="Full class name (e.g., IIIA)")

    model_config = {"from_attributes": True}


# ============ Class Matter Assignment Schemas ============

class ClassMatterAssignmentBase(BaseModel):
    """Base schema for class-matter-teacher assignments."""
    matter_id: int
    teacher_id: int
    hours_per_week: int = Field(..., ge=1, description="Fixed number of hours per week")


class ClassMatterAssignmentCreate(ClassMatterAssignmentBase):
    """Schema for creating an assignment."""
    pass


class ClassMatterAssignmentUpdate(BaseModel):
    """Schema for updating an assignment."""
    teacher_id: int | None = None
    hours_per_week: int | None = Field(None, ge=1)


class ClassMatterAssignmentResponse(ClassMatterAssignmentBase):
    """Schema for assignment response."""
    id: int
    class_id: int
    matter: MatterResponse
    teacher: TeacherResponse

    model_config = {"from_attributes": True}


class SchoolClassWithAssignmentsResponse(SchoolClassResponse):
    """Schema for school class response including matter assignments."""
    matter_assignments: list[ClassMatterAssignmentResponse] = []

    model_config = {"from_attributes": True}


# ============ Saved Schedule Schemas ============

class SavedScheduleBase(BaseModel):
    """Base schema for saved schedules."""
    nickname: str | None = Field(None, max_length=255, description="User-friendly name for the schedule")


class SavedScheduleCreate(SavedScheduleBase):
    """Schema for creating a saved schedule (internal use)."""
    name: str
    status: str
    solve_time_seconds: float
    total_slots: int
    schedule_data: str  # JSON string


class SavedScheduleUpdate(BaseModel):
    """Schema for updating a saved schedule."""
    nickname: str | None = Field(None, max_length=255)


class SavedScheduleListResponse(BaseModel):
    """Schema for saved schedule in list view (without full data)."""
    id: int
    name: str
    nickname: str | None
    status: str
    solve_time_seconds: float
    total_slots: int
    created_at: str  # ISO format

    model_config = {"from_attributes": True}


class SavedScheduleResponse(SavedScheduleListResponse):
    """Schema for full saved schedule response including data."""
    schedule_data: dict  # Parsed JSON

    model_config = {"from_attributes": True}


# Rebuild models to resolve forward references
MatterWithTeachersResponse.model_rebuild()
