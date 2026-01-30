"""Teachers API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from squola.database import get_db
from squola.models import Teacher, Matter, TeacherBlacklistedSlot
from squola.schemas import (
    TeacherCreate,
    TeacherUpdate,
    TeacherResponse,
    TeacherWithMattersResponse,
    BlacklistedSlotCreate,
    BlacklistedSlotResponse,
)

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("", response_model=list[TeacherResponse])
def list_teachers(db: Session = Depends(get_db)) -> list[Teacher]:
    """List all teachers in the roster."""
    stmt = select(Teacher)
    return list(db.scalars(stmt).all())


@router.get("/{teacher_id}", response_model=TeacherWithMattersResponse)
def get_teacher(teacher_id: int, db: Session = Depends(get_db)) -> Teacher:
    """Get a specific teacher by ID with their matters and blacklisted slots."""
    stmt = (
        select(Teacher)
        .where(Teacher.id == teacher_id)
        .options(
            selectinload(Teacher.matters),
            selectinload(Teacher.blacklisted_slots)
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
def create_teacher(teacher_data: TeacherCreate, db: Session = Depends(get_db)) -> Teacher:
    """Add a new teacher to the roster."""
    # Fetch matters if provided
    matters = []
    if teacher_data.matter_ids:
        stmt = select(Matter).where(Matter.id.in_(teacher_data.matter_ids))
        matters = list(db.scalars(stmt).all())
        if len(matters) != len(teacher_data.matter_ids):
            found_ids = {m.id for m in matters}
            missing_ids = set(teacher_data.matter_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Matters with ids {missing_ids} not found"
            )
    
    teacher = Teacher(
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
    db: Session = Depends(get_db)
) -> Teacher:
    """Update an existing teacher."""
    stmt = (
        select(Teacher)
        .where(Teacher.id == teacher_id)
        .options(selectinload(Teacher.matters), selectinload(Teacher.blacklisted_slots))
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
            stmt = select(Matter).where(Matter.id.in_(teacher_data.matter_ids))
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
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)) -> None:
    """Remove a teacher from the roster."""
    stmt = select(Teacher).where(Teacher.id == teacher_id)
    teacher = db.scalars(stmt).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with id {teacher_id} not found"
        )
    
    db.delete(teacher)
    db.commit()


# ============ Blacklisted Slots Endpoints ============

@router.get("/{teacher_id}/blacklisted-slots", response_model=list[BlacklistedSlotResponse])
def list_blacklisted_slots(teacher_id: int, db: Session = Depends(get_db)) -> list[TeacherBlacklistedSlot]:
    """List all blacklisted time slots for a teacher."""
    # Verify teacher exists
    stmt = select(Teacher).where(Teacher.id == teacher_id)
    teacher = db.scalars(stmt).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with id {teacher_id} not found"
        )
    
    stmt = select(TeacherBlacklistedSlot).where(TeacherBlacklistedSlot.teacher_id == teacher_id)
    return list(db.scalars(stmt).all())


@router.post(
    "/{teacher_id}/blacklisted-slots",
    response_model=BlacklistedSlotResponse,
    status_code=status.HTTP_201_CREATED
)
def add_blacklisted_slot(
    teacher_id: int,
    slot_data: BlacklistedSlotCreate,
    db: Session = Depends(get_db)
) -> TeacherBlacklistedSlot:
    """Add a blacklisted time slot for a teacher (e.g., hours at another school)."""
    # Verify teacher exists
    stmt = select(Teacher).where(Teacher.id == teacher_id)
    teacher = db.scalars(stmt).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with id {teacher_id} not found"
        )
    
    # Check if slot already exists
    stmt = select(TeacherBlacklistedSlot).where(
        TeacherBlacklistedSlot.teacher_id == teacher_id,
        TeacherBlacklistedSlot.day_of_week == slot_data.day_of_week,
        TeacherBlacklistedSlot.hour_slot == slot_data.hour_slot,
    )
    existing = db.scalars(stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This time slot is already blacklisted for this teacher"
        )
    
    slot = TeacherBlacklistedSlot(
        teacher_id=teacher_id,
        day_of_week=slot_data.day_of_week,
        hour_slot=slot_data.hour_slot,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


@router.delete("/{teacher_id}/blacklisted-slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_blacklisted_slot(teacher_id: int, slot_id: int, db: Session = Depends(get_db)) -> None:
    """Remove a blacklisted time slot for a teacher."""
    stmt = select(TeacherBlacklistedSlot).where(
        TeacherBlacklistedSlot.id == slot_id,
        TeacherBlacklistedSlot.teacher_id == teacher_id,
    )
    slot = db.scalars(stmt).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blacklisted slot with id {slot_id} not found for teacher {teacher_id}"
        )
    
    db.delete(slot)
    db.commit()
