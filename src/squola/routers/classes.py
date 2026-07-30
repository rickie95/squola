"""School Classes API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from squola.database import get_db
from squola.models import SchoolClass, ClassMatterAssignment, Matter, Teacher
from squola.schemas import (
    SchoolClassCreate,
    SchoolClassUpdate,
    SchoolClassResponse,
    SchoolClassWithAssignmentsResponse,
    ClassMatterAssignmentCreate,
    ClassMatterAssignmentUpdate,
    ClassMatterAssignmentResponse,
)

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("", response_model=list[SchoolClassResponse])
def list_classes(db: Session = Depends(get_db)) -> list[SchoolClass]:
    """List all school classes."""
    stmt = select(SchoolClass)
    return list(db.scalars(stmt).all())


@router.get("/{class_id}", response_model=SchoolClassWithAssignmentsResponse)
def get_class(class_id: int, db: Session = Depends(get_db)) -> SchoolClass:
    """Get a specific school class by ID with its matter assignments."""
    stmt = (
        select(SchoolClass)
        .where(SchoolClass.id == class_id)
        .options(
            selectinload(SchoolClass.matter_assignments)
            .selectinload(ClassMatterAssignment.matter),
            selectinload(SchoolClass.matter_assignments)
            .selectinload(ClassMatterAssignment.teacher),
        )
    )
    school_class = db.scalars(stmt).first()
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class with id {class_id} not found"
        )
    return school_class


@router.post("", response_model=SchoolClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(class_data: SchoolClassCreate, db: Session = Depends(get_db)) -> SchoolClass:
    """Create a new school class."""
    # Check if class with same year and section already exists
    stmt = select(SchoolClass).where(
        SchoolClass.year == class_data.year,
        SchoolClass.section == class_data.section,
    )
    existing = db.scalars(stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Class {class_data.year}{class_data.section} already exists"
        )
    
    school_class = SchoolClass(
        year=class_data.year,
        section=class_data.section,
    )
    db.add(school_class)
    db.commit()
    db.refresh(school_class)
    return school_class


@router.put("/{class_id}", response_model=SchoolClassResponse)
def update_class(
    class_id: int,
    class_data: SchoolClassUpdate,
    db: Session = Depends(get_db)
) -> SchoolClass:
    """Update an existing school class."""
    stmt = select(SchoolClass).where(SchoolClass.id == class_id)
    school_class = db.scalars(stmt).first()
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class with id {class_id} not found"
        )
    
    # Update fields if provided
    new_year = class_data.year if class_data.year is not None else school_class.year
    new_section = class_data.section if class_data.section is not None else school_class.section
    
    # Check for conflicts if changing year or section
    if new_year != school_class.year or new_section != school_class.section:
        stmt = select(SchoolClass).where(
            SchoolClass.year == new_year,
            SchoolClass.section == new_section,
            SchoolClass.id != class_id,
        )
        existing = db.scalars(stmt).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Class {new_year}{new_section} already exists"
            )
    
    school_class.year = new_year
    school_class.section = new_section
    
    db.commit()
    db.refresh(school_class)
    return school_class


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(class_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a school class."""
    stmt = select(SchoolClass).where(SchoolClass.id == class_id)
    school_class = db.scalars(stmt).first()
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class with id {class_id} not found"
        )
    
    db.delete(school_class)
    db.commit()


# ============ Class Matter Assignments Endpoints ============

@router.get("/{class_id}/assignments", response_model=list[ClassMatterAssignmentResponse])
def list_class_assignments(class_id: int, db: Session = Depends(get_db)) -> list[ClassMatterAssignment]:
    """List all matter-teacher assignments for a class."""
    # Verify class exists
    stmt = select(SchoolClass).where(SchoolClass.id == class_id)
    school_class = db.scalars(stmt).first()
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class with id {class_id} not found"
        )
    
    stmt = (
        select(ClassMatterAssignment)
        .where(ClassMatterAssignment.class_id == class_id)
        .options(
            selectinload(ClassMatterAssignment.matter),
            selectinload(ClassMatterAssignment.teacher),
        )
    )
    return list(db.scalars(stmt).all())


@router.post(
    "/{class_id}/assignments",
    response_model=ClassMatterAssignmentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_class_assignment(
    class_id: int,
    assignment_data: ClassMatterAssignmentCreate,
    db: Session = Depends(get_db)
) -> ClassMatterAssignment:
    """
    Assign a teacher to teach a specific matter in this class.
    
    Each class can have only one teacher per matter.
    """
    # Verify class exists
    stmt = select(SchoolClass).where(SchoolClass.id == class_id)
    school_class = db.scalars(stmt).first()
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class with id {class_id} not found"
        )
    
    # Verify matter exists
    stmt = select(Matter).where(Matter.id == assignment_data.matter_id)
    matter = db.scalars(stmt).first()
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matter with id {assignment_data.matter_id} not found"
        )
    
    # Verify teacher exists
    stmt = select(Teacher).where(Teacher.id == assignment_data.teacher_id)
    teacher = db.scalars(stmt).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with id {assignment_data.teacher_id} not found"
        )
    
    # Check if matter is already assigned in this class
    stmt = select(ClassMatterAssignment).where(
        ClassMatterAssignment.class_id == class_id,
        ClassMatterAssignment.matter_id == assignment_data.matter_id,
    )
    existing = db.scalars(stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Matter {matter.name} is already assigned in this class"
        )
    
    assignment = ClassMatterAssignment(
        class_id=class_id,
        matter_id=assignment_data.matter_id,
        teacher_id=assignment_data.teacher_id,
        hours_per_week=assignment_data.hours_per_week,
        requirements=assignment_data.requirements
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    # Reload with relationships
    stmt = (
        select(ClassMatterAssignment)
        .where(ClassMatterAssignment.id == assignment.id)
        .options(
            selectinload(ClassMatterAssignment.matter),
            selectinload(ClassMatterAssignment.teacher),
        )
    )

    res = db.scalars(stmt).first()
    return res


@router.put("/{class_id}/assignments/{assignment_id}", response_model=ClassMatterAssignmentResponse)
def update_class_assignment(
    class_id: int,
    assignment_id: int,
    assignment_data: ClassMatterAssignmentUpdate,
    db: Session = Depends(get_db)
) -> ClassMatterAssignment:
    """Update a class matter assignment (change teacher or hours)."""
    stmt = (
        select(ClassMatterAssignment)
        .where(
            ClassMatterAssignment.id == assignment_id,
            ClassMatterAssignment.class_id == class_id,
        )
        .options(
            selectinload(ClassMatterAssignment.matter),
            selectinload(ClassMatterAssignment.teacher),
        )
    )
    assignment = db.scalars(stmt).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment with id {assignment_id} not found in class {class_id}"
        )
    
    if assignment_data.teacher_id is not None:
        # Verify new teacher exists
        stmt = select(Teacher).where(Teacher.id == assignment_data.teacher_id)
        teacher = db.scalars(stmt).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Teacher with id {assignment_data.teacher_id} not found"
            )
        assignment.teacher_id = assignment_data.teacher_id
    
    if assignment_data.hours_per_week is not None:
        assignment.hours_per_week = assignment_data.hours_per_week

    if assignment_data.requirements is not None:
        assignment.requirements = assignment_data.requirements
    
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/{class_id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class_assignment(class_id: int, assignment_id: int, db: Session = Depends(get_db)) -> None:
    """Remove a matter-teacher assignment from a class."""
    stmt = select(ClassMatterAssignment).where(
        ClassMatterAssignment.id == assignment_id,
        ClassMatterAssignment.class_id == class_id,
    )
    assignment = db.scalars(stmt).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment with id {assignment_id} not found in class {class_id}"
        )
    
    db.delete(assignment)
    db.commit()
