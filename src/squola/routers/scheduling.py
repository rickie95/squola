"""API router for schedule generation endpoints."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from squola.database import get_db
from squola.scheduler import generate_schedule, GeneratedSchedule


router = APIRouter(prefix="/scheduling", tags=["scheduling"])


class GenerateScheduleRequest(BaseModel):
    """Request parameters for schedule generation."""
    time_limit_seconds: float = Field(
        default=60.0,
        ge=1.0,
        le=600.0,
        description="Maximum time in seconds to spend solving the schedule"
    )
    save_to_file: bool = Field(
        default=False,
        description="Whether to save the schedule to a JSON file"
    )
    output_path: str | None = Field(
        default=None,
        description="Path to save the JSON file (defaults to ./schedule_output.json)"
    )


class ScheduleMetadata(BaseModel):
    """Metadata about the generated schedule."""
    status: str
    solve_time_seconds: float
    generated_at: str
    total_slots: int


class ScheduleSlotResponse(BaseModel):
    """A single slot in the schedule."""
    day: str
    hour: str
    teacher: str
    matter: str


class ScheduleSlotWithClassResponse(ScheduleSlotResponse):
    """A slot that includes the class name."""
    class_name: str = Field(alias="class")
    
    model_config = {"populate_by_name": True}


class GenerateScheduleResponse(BaseModel):
    """Response containing the generated schedule."""
    metadata: ScheduleMetadata
    schedule: dict[str, Any]


@router.post("/generate", response_model=GenerateScheduleResponse)
def generate_schedule_endpoint(
    request: GenerateScheduleRequest,
    db: Session = Depends(get_db),
) -> GenerateScheduleResponse:
    """
    Generate a new school schedule.
    
    Uses OR-Tools CP-SAT solver to find a valid schedule that satisfies
    all constraints:
    
    - Each class-matter assignment gets exactly its required hours per week
    - Teachers cannot teach two classes at the same time
    - Classes cannot have two lessons at the same time
    - Teachers are not scheduled during their blacklisted slots
    - Teacher preferences (early/late/minimize gaps/maximize gaps) are optimized
    
    Returns the schedule grouped by class, by teacher, and by day.
    """
    schedule = generate_schedule(db, request.time_limit_seconds)
    
    if schedule.status == "NO_DATA":
        raise HTTPException(
            status_code=400,
            detail="No class-matter assignments found. Please create assignments first."
        )
    
    if schedule.status == "INFEASIBLE":
        raise HTTPException(
            status_code=422,
            detail="No valid schedule could be found with the current constraints. "
                   "Consider relaxing constraints or adjusting hours per week."
        )
    
    if schedule.status == "MODEL_INVALID":
        raise HTTPException(
            status_code=500,
            detail="The scheduling model is invalid. Please contact support."
        )
    
    # Save to file if requested
    if request.save_to_file:
        output_path = request.output_path or "./schedule_output.json"
        try:
            schedule.save_to_json(output_path)
        except Exception as e:
            # Don't fail the whole request if file save fails
            pass
    
    return GenerateScheduleResponse(**schedule.to_dict())


@router.get("/preview")
def preview_scheduling_data(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Preview the data that will be used for scheduling.
    
    Returns a summary of:
    - Number of teachers and their blacklisted slots
    - Number of classes
    - Number of assignments and total hours to schedule
    - Potential issues (teachers without assignments, etc.)
    """
    from squola.scheduler import fetch_scheduling_data, DAYS_OF_WEEK, HOURS_PER_DAY
    
    data = fetch_scheduling_data(db)
    
    # Calculate total hours needed
    total_hours = sum(a.hours_per_week for a in data.assignments)
    total_slots_available = DAYS_OF_WEEK * HOURS_PER_DAY * len(data.classes)
    
    # Find potential issues
    issues = []
    
    # Check if we have enough slots
    if total_hours > total_slots_available:
        issues.append(
            f"Total hours needed ({total_hours}) exceeds available slots ({total_slots_available})"
        )
    
    # Check for teachers with too many hours
    teacher_hours: dict[int, int] = {}
    for assignment in data.assignments:
        teacher_hours[assignment.teacher_id] = (
            teacher_hours.get(assignment.teacher_id, 0) + assignment.hours_per_week
        )
    
    max_teacher_hours = DAYS_OF_WEEK * HOURS_PER_DAY
    for teacher_id, hours in teacher_hours.items():
        if hours > max_teacher_hours:
            teacher = next(t for t in data.teachers if t.id == teacher_id)
            issues.append(
                f"Teacher {teacher.first_name} {teacher.last_name} has {hours} hours "
                f"but max possible is {max_teacher_hours}"
            )
    
    # Check for blacklisted slots reducing availability
    blacklist_counts: dict[int, int] = {}
    for slot in data.blacklisted_slots:
        blacklist_counts[slot.teacher_id] = blacklist_counts.get(slot.teacher_id, 0) + 1
    
    for teacher_id, blacklist_count in blacklist_counts.items():
        hours = teacher_hours.get(teacher_id, 0)
        available = max_teacher_hours - blacklist_count
        if hours > available:
            teacher = next(t for t in data.teachers if t.id == teacher_id)
            issues.append(
                f"Teacher {teacher.first_name} {teacher.last_name} needs {hours} hours "
                f"but only has {available} slots available (after blacklist)"
            )
    
    return {
        "summary": {
            "teachers_count": len(data.teachers),
            "classes_count": len(data.classes),
            "assignments_count": len(data.assignments),
            "total_hours_to_schedule": total_hours,
            "total_slots_available": total_slots_available,
            "blacklisted_slots_count": len(data.blacklisted_slots),
        },
        "teachers": [
            {
                "id": t.id,
                "name": f"{t.first_name} {t.last_name}",
                "hours_assigned": teacher_hours.get(t.id, 0),
                "blacklisted_slots": blacklist_counts.get(t.id, 0),
                "preference": t.schedule_preference,
            }
            for t in data.teachers
        ],
        "classes": [
            {
                "id": c.id,
                "name": c.name,
                "assignments_count": len([a for a in data.assignments if a.class_id == c.id]),
                "total_hours": sum(a.hours_per_week for a in data.assignments if a.class_id == c.id),
            }
            for c in data.classes
        ],
        "issues": issues,
    }
