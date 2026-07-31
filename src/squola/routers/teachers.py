"""Teachers API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from squola.auth import get_current_workspace
from squola.database import get_db
from squola.models import Matter, Teacher, TeacherUnavailability, Workspace
from squola.schemas import (
    TeacherCreate,
    TeacherUpdate,
    TeacherResponse,
    TeacherWithMattersResponse,
    UnavailabilityCreate,
    UnavailabilityResponse,
)

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("", response_model=list[TeacherResponse])
def list_teachers(
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> list[Teacher]:
    """List all teachers in the roster."""
    stmt = select(Teacher).where(Teacher.workspace_id == workspace.id)
    return list(db.scalars(stmt).all())


@router.get("/{teacher_id}", response_model=TeacherWithMattersResponse)
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> Teacher:
    """Get a specific teacher by ID with their matters and blacklisted slots."""
    stmt = (
        select(Teacher)
        .where(Teacher.id == teacher_id, Teacher.workspace_id == workspace.id)
        .options(
            selectinload(Teacher.matters),
            selectinload(Teacher.unavailabilities)
        )
    )
    teacher = db.scalars(stmt).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with id {teacher_id} not found"
        )
    return teacher


@router.post("", response_model=TeacherWithMattersResponse, status_code=status.HTTP_201_CREATED)
def create_teacher(
    teacher_data: TeacherCreate,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> Teacher:
    """Add a new teacher to the roster."""
    # Fetch matters if provided
    matters = []
    if teacher_data.matter_ids:
        stmt = select(Matter).where(
            Matter.id.in_(teacher_data.matter_ids),
            Matter.workspace_id == workspace.id,
        )
        matters = list(db.scalars(stmt).all())
        if len(matters) != len(teacher_data.matter_ids):
            found_ids = {m.id for m in matters}
            missing_ids = set(teacher_data.matter_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Matters with ids {missing_ids} not found"
            )
    
    teacher = Teacher(
        workspace_id=workspace.id,
        first_name=teacher_data.first_name,
        last_name=teacher_data.last_name,
        email=teacher_data.email,
        schedule_preference=teacher_data.schedule_preference.value,
        matters=matters,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.put("/{teacher_id}", response_model=TeacherWithMattersResponse)
def update_teacher(
    teacher_id: int,
    teacher_data: TeacherUpdate,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> Teacher:
    """Update an existing teacher."""
    stmt = (
        select(Teacher)
        .where(Teacher.id == teacher_id, Teacher.workspace_id == workspace.id)
        .options(selectinload(Teacher.matters), selectinload(Teacher.unavailabilities))
    )
    teacher = db.scalars(stmt).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with id {teacher_id} not found"
        )
    
    # Update fields if provided
    if teacher_data.first_name is not None:
        teacher.first_name = teacher_data.first_name
    if teacher_data.last_name is not None:
        teacher.last_name = teacher_data.last_name
    if teacher_data.email is not None:
        teacher.email = teacher_data.email
    if teacher_data.schedule_preference is not None:
        teacher.schedule_preference = teacher_data.schedule_preference.value
    
    # Update matters if provided
    if teacher_data.matter_ids is not None:
        if teacher_data.matter_ids:
            stmt = select(Matter).where(
                Matter.id.in_(teacher_data.matter_ids),
                Matter.workspace_id == workspace.id,
            )
            matters = list(db.scalars(stmt).all())
            if len(matters) != len(teacher_data.matter_ids):
                found_ids = {m.id for m in matters}
                missing_ids = set(teacher_data.matter_ids) - found_ids
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Matters with ids {missing_ids} not found"
                )
            teacher.matters = matters
        else:
            teacher.matters = []
    
    db.commit()
    db.refresh(teacher)
    return teacher


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> None:
    """Remove a teacher from the roster."""
    stmt = select(Teacher).where(Teacher.id == teacher_id, Teacher.workspace_id == workspace.id)
    teacher = db.scalars(stmt).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with id {teacher_id} not found"
        )
    
    db.delete(teacher)
    db.commit()


# ============ Unavailability Endpoints ============

@router.get("/{teacher_id}/unavailabilities", response_model=list[UnavailabilityResponse])
def list_unavailabilities(
    teacher_id: int,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> list[TeacherUnavailability]:
    """List all unavailability slots for a teacher."""
    stmt = select(Teacher).where(Teacher.id == teacher_id, Teacher.workspace_id == workspace.id)
    teacher = db.scalars(stmt).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with id {teacher_id} not found"
        )

    stmt = select(TeacherUnavailability).where(
        TeacherUnavailability.teacher_id == teacher_id,
        TeacherUnavailability.workspace_id == workspace.id,
    )
    return list(db.scalars(stmt).all())


@router.post(
    "/{teacher_id}/unavailabilities",
    response_model=UnavailabilityResponse,
    status_code=status.HTTP_201_CREATED
)
def add_unavailability(
    teacher_id: int,
    slot_data: UnavailabilityCreate,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> TeacherUnavailability:
    """Add an unavailability slot for a teacher (e.g., hours at another school)."""
    stmt = select(Teacher).where(Teacher.id == teacher_id, Teacher.workspace_id == workspace.id)
    teacher = db.scalars(stmt).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with id {teacher_id} not found"
        )

    stmt = select(TeacherUnavailability).where(
        TeacherUnavailability.teacher_id == teacher_id,
        TeacherUnavailability.workspace_id == workspace.id,
        TeacherUnavailability.day_of_week == slot_data.day_of_week,
        TeacherUnavailability.hour_slot == slot_data.hour_slot,
    )
    if db.scalars(stmt).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This time slot is already marked as unavailable for this teacher"
        )

    slot = TeacherUnavailability(
        workspace_id=workspace.id,
        teacher_id=teacher_id,
        day_of_week=slot_data.day_of_week,
        hour_slot=slot_data.hour_slot,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


@router.delete("/{teacher_id}/unavailabilities/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_unavailability(
    teacher_id: int,
    slot_id: int,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> None:
    """Remove an unavailability slot for a teacher."""
    stmt = select(TeacherUnavailability).where(
        TeacherUnavailability.id == slot_id,
        TeacherUnavailability.teacher_id == teacher_id,
        TeacherUnavailability.workspace_id == workspace.id,
    )
    slot = db.scalars(stmt).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unavailability slot with id {slot_id} not found for teacher {teacher_id}"
        )
    
    db.delete(slot)
    db.commit()
