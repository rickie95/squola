"""School Classes API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from squola.auth import get_current_workspace
from squola.database import get_db
from squola.models import (
    ClassMatterAssignment,
    FixedClassLesson,
    Matter,
    SchoolClass,
    Teacher,
    TeacherUnavailability,
    Workspace,
)
from squola.schemas import (
    ClassMatterAssignmentCreate,
    ClassMatterAssignmentResponse,
    ClassMatterAssignmentUpdate,
    FixedClassLessonCreate,
    FixedClassLessonResponse,
    FixedClassLessonUpdate,
    SchoolClassCreate,
    SchoolClassResponse,
    SchoolClassUpdate,
    SchoolClassWithAssignmentsResponse,
)

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("", response_model=list[SchoolClassResponse])
def list_classes(
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> list[SchoolClass]:
    """List all school classes."""
    stmt = select(SchoolClass).where(SchoolClass.workspace_id == workspace.id)
    return list(db.scalars(stmt).all())


@router.get("/{class_id}", response_model=SchoolClassWithAssignmentsResponse)
def get_class(
    class_id: int,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> SchoolClass:
    """Get a specific school class by ID with its matter assignments."""
    stmt = (
        select(SchoolClass)
        .where(SchoolClass.id == class_id, SchoolClass.workspace_id == workspace.id)
        .options(
            selectinload(SchoolClass.matter_assignments).selectinload(ClassMatterAssignment.matter),
            selectinload(SchoolClass.matter_assignments).selectinload(
                ClassMatterAssignment.teacher
            ),
            selectinload(SchoolClass.fixed_lessons)
            .selectinload(FixedClassLesson.assignment)
            .selectinload(ClassMatterAssignment.matter),
            selectinload(SchoolClass.fixed_lessons)
            .selectinload(FixedClassLesson.assignment)
            .selectinload(ClassMatterAssignment.teacher),
        )
    )
    school_class = db.scalars(stmt).first()
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with id {class_id} not found"
        )
    return school_class


def _get_class_assignment(
    class_id: int,
    assignment_id: int,
    workspace_id: int,
    db: Session,
) -> ClassMatterAssignment:
    stmt = (
        select(ClassMatterAssignment)
        .where(
            ClassMatterAssignment.id == assignment_id,
            ClassMatterAssignment.class_id == class_id,
            ClassMatterAssignment.workspace_id == workspace_id,
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
            detail=f"Assignment with id {assignment_id} not found in class {class_id}",
        )
    return assignment


def _validate_fixed_lesson(
    *,
    assignment: ClassMatterAssignment,
    day_of_week: int,
    hour_slot: int,
    workspace_id: int,
    db: Session,
    excluded_fixed_lesson_id: int | None = None,
) -> None:
    fixed_count_stmt = select(func.count()).select_from(FixedClassLesson).where(
        FixedClassLesson.assignment_id == assignment.id,
        FixedClassLesson.workspace_id == workspace_id,
    )
    if excluded_fixed_lesson_id is not None:
        fixed_count_stmt = fixed_count_stmt.where(
            FixedClassLesson.id != excluded_fixed_lesson_id
        )
    fixed_count = db.scalar(fixed_count_stmt) or 0
    if fixed_count >= assignment.hours_per_week:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Assignment {assignment.matter.name} already has "
                f"{assignment.hours_per_week} fixed lessons"
            ),
        )

    unavailable_stmt = select(TeacherUnavailability).where(
        TeacherUnavailability.workspace_id == workspace_id,
        TeacherUnavailability.teacher_id == assignment.teacher_id,
        TeacherUnavailability.day_of_week == day_of_week,
        TeacherUnavailability.hour_slot == hour_slot,
    )
    if db.scalars(unavailable_stmt).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The teacher is unavailable in this time slot",
        )

    teacher_conflict_stmt = (
        select(FixedClassLesson)
        .join(FixedClassLesson.assignment)
        .where(
            FixedClassLesson.workspace_id == workspace_id,
            FixedClassLesson.day_of_week == day_of_week,
            FixedClassLesson.hour_slot == hour_slot,
            ClassMatterAssignment.teacher_id == assignment.teacher_id,
        )
    )
    if excluded_fixed_lesson_id is not None:
        teacher_conflict_stmt = teacher_conflict_stmt.where(
            FixedClassLesson.id != excluded_fixed_lesson_id
        )
    if db.scalars(teacher_conflict_stmt).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The teacher already has a fixed lesson in this time slot",
        )


def _validate_teacher_change_for_fixed_lessons(
    assignment: ClassMatterAssignment,
    teacher_id: int,
    workspace_id: int,
    db: Session,
) -> None:
    fixed_lessons = list(
        db.scalars(
            select(FixedClassLesson).where(
                FixedClassLesson.assignment_id == assignment.id,
                FixedClassLesson.workspace_id == workspace_id,
            )
        ).all()
    )
    if not fixed_lessons:
        return

    for fixed_lesson in fixed_lessons:
        unavailable_stmt = select(TeacherUnavailability).where(
            TeacherUnavailability.workspace_id == workspace_id,
            TeacherUnavailability.teacher_id == teacher_id,
            TeacherUnavailability.day_of_week == fixed_lesson.day_of_week,
            TeacherUnavailability.hour_slot == fixed_lesson.hour_slot,
        )
        if db.scalars(unavailable_stmt).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The new teacher is unavailable during an existing fixed lesson",
            )

        conflict_stmt = (
            select(FixedClassLesson)
            .join(FixedClassLesson.assignment)
            .where(
                FixedClassLesson.workspace_id == workspace_id,
                FixedClassLesson.id != fixed_lesson.id,
                FixedClassLesson.day_of_week == fixed_lesson.day_of_week,
                FixedClassLesson.hour_slot == fixed_lesson.hour_slot,
                ClassMatterAssignment.teacher_id == teacher_id,
            )
        )
        if db.scalars(conflict_stmt).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The new teacher has another fixed lesson in this time slot",
            )


@router.post(
    "/{class_id}/fixed-lessons",
    response_model=FixedClassLessonResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fixed_lesson(
    class_id: int,
    lesson_data: FixedClassLessonCreate,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> FixedClassLesson:
    """Fix an existing class assignment in a specific weekly slot."""
    assignment = _get_class_assignment(class_id, lesson_data.assignment_id, workspace.id, db)

    existing_slot = db.scalars(
        select(FixedClassLesson).where(
            FixedClassLesson.class_id == class_id,
            FixedClassLesson.workspace_id == workspace.id,
            FixedClassLesson.day_of_week == lesson_data.day_of_week,
            FixedClassLesson.hour_slot == lesson_data.hour_slot,
        )
    ).first()
    if existing_slot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This class already has a fixed lesson in this time slot",
        )

    _validate_fixed_lesson(
        assignment=assignment,
        day_of_week=lesson_data.day_of_week,
        hour_slot=lesson_data.hour_slot,
        workspace_id=workspace.id,
        db=db,
    )
    fixed_lesson = FixedClassLesson(
        workspace_id=workspace.id,
        class_id=class_id,
        assignment_id=assignment.id,
        day_of_week=lesson_data.day_of_week,
        hour_slot=lesson_data.hour_slot,
    )
    db.add(fixed_lesson)
    db.commit()
    db.refresh(fixed_lesson)
    return fixed_lesson


@router.put(
    "/{class_id}/fixed-lessons/{fixed_lesson_id}",
    response_model=FixedClassLessonResponse,
)
def update_fixed_lesson(
    class_id: int,
    fixed_lesson_id: int,
    lesson_data: FixedClassLessonUpdate,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> FixedClassLesson:
    """Replace the assignment fixed in a class timetable slot."""
    fixed_lesson = db.scalars(
        select(FixedClassLesson)
        .where(
            FixedClassLesson.id == fixed_lesson_id,
            FixedClassLesson.class_id == class_id,
            FixedClassLesson.workspace_id == workspace.id,
        )
        .options(
            selectinload(FixedClassLesson.assignment).selectinload(
                ClassMatterAssignment.matter
            ),
            selectinload(FixedClassLesson.assignment).selectinload(
                ClassMatterAssignment.teacher
            ),
        )
    ).first()
    if not fixed_lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fixed lesson with id {fixed_lesson_id} not found in class {class_id}",
        )

    assignment = _get_class_assignment(class_id, lesson_data.assignment_id, workspace.id, db)
    if assignment.id != fixed_lesson.assignment_id:
        _validate_fixed_lesson(
            assignment=assignment,
            day_of_week=fixed_lesson.day_of_week,
            hour_slot=fixed_lesson.hour_slot,
            workspace_id=workspace.id,
            db=db,
            excluded_fixed_lesson_id=fixed_lesson.id,
        )
        fixed_lesson.assignment_id = assignment.id

    db.commit()
    db.refresh(fixed_lesson)
    return fixed_lesson


@router.delete(
    "/{class_id}/fixed-lessons/{fixed_lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_fixed_lesson(
    class_id: int,
    fixed_lesson_id: int,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> None:
    """Remove a fixed lesson from a class timetable slot."""
    fixed_lesson = db.scalars(
        select(FixedClassLesson).where(
            FixedClassLesson.id == fixed_lesson_id,
            FixedClassLesson.class_id == class_id,
            FixedClassLesson.workspace_id == workspace.id,
        )
    ).first()
    if not fixed_lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fixed lesson with id {fixed_lesson_id} not found in class {class_id}",
        )
    db.delete(fixed_lesson)
    db.commit()


@router.post("", response_model=SchoolClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    class_data: SchoolClassCreate,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> SchoolClass:
    """Create a new school class."""
    # Check if class with same year and section already exists
    stmt = select(SchoolClass).where(
        SchoolClass.year == class_data.year,
        SchoolClass.section == class_data.section,
        SchoolClass.workspace_id == workspace.id,
    )
    existing = db.scalars(stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Class {class_data.year}{class_data.section} already exists",
        )

    school_class = SchoolClass(
        workspace_id=workspace.id,
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
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> SchoolClass:
    """Update an existing school class."""
    stmt = select(SchoolClass).where(
        SchoolClass.id == class_id, SchoolClass.workspace_id == workspace.id
    )
    school_class = db.scalars(stmt).first()
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with id {class_id} not found"
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
            SchoolClass.workspace_id == workspace.id,
        )
        existing = db.scalars(stmt).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Class {new_year}{new_section} already exists",
            )

    school_class.year = new_year
    school_class.section = new_section

    db.commit()
    db.refresh(school_class)
    return school_class


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> None:
    """Delete a school class."""
    stmt = select(SchoolClass).where(
        SchoolClass.id == class_id, SchoolClass.workspace_id == workspace.id
    )
    school_class = db.scalars(stmt).first()
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with id {class_id} not found"
        )

    db.delete(school_class)
    db.commit()


@router.post(
    "/{class_id}/clone", response_model=SchoolClassResponse, status_code=status.HTTP_201_CREATED
)
def clone_class(
    class_id: int,
    class_data: SchoolClassCreate,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> SchoolClass:
    """Clone a school class and its matter assignments."""
    # Verify source class exists
    stmt = select(SchoolClass).where(
        SchoolClass.id == class_id, SchoolClass.workspace_id == workspace.id
    )
    source_class = db.scalars(stmt).first()
    if not source_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source class with id {class_id} not found",
        )

    # Check if target class already exists
    stmt = select(SchoolClass).where(
        SchoolClass.year == class_data.year,
        SchoolClass.section == class_data.section,
        SchoolClass.workspace_id == workspace.id,
    )
    existing = db.scalars(stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Class {class_data.year}{class_data.section} already exists",
        )

    # Create the new class
    new_class = SchoolClass(
        workspace_id=workspace.id,
        year=class_data.year,
        section=class_data.section,
    )
    db.add(new_class)
    db.flush()  # Get new_class.id without committing yet

    # Copy assignments from source class
    assignments_stmt = select(ClassMatterAssignment).where(
        ClassMatterAssignment.class_id == class_id,
        ClassMatterAssignment.workspace_id == workspace.id,
    )
    source_assignments = db.scalars(assignments_stmt).all()

    for assignment in source_assignments:
        new_assignment = ClassMatterAssignment(
            workspace_id=workspace.id,
            class_id=new_class.id,
            matter_id=assignment.matter_id,
            teacher_id=assignment.teacher_id,
            hours_per_week=assignment.hours_per_week,
            requirements=assignment.requirements,
        )
        db.add(new_assignment)

    db.commit()
    db.refresh(new_class)
    return new_class


@router.get("/{class_id}/assignments", response_model=list[ClassMatterAssignmentResponse])
def list_class_assignments(
    class_id: int,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> list[ClassMatterAssignment]:
    """List all matter-teacher assignments for a class."""
    # Verify class exists
    stmt = select(SchoolClass).where(
        SchoolClass.id == class_id, SchoolClass.workspace_id == workspace.id
    )
    school_class = db.scalars(stmt).first()
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with id {class_id} not found"
        )

    stmt = (
        select(ClassMatterAssignment)
        .where(
            ClassMatterAssignment.class_id == class_id,
            ClassMatterAssignment.workspace_id == workspace.id,
        )
        .options(
            selectinload(ClassMatterAssignment.matter),
            selectinload(ClassMatterAssignment.teacher),
        )
    )
    return list(db.scalars(stmt).all())


@router.post(
    "/{class_id}/assignments",
    response_model=ClassMatterAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_class_assignment(
    class_id: int,
    assignment_data: ClassMatterAssignmentCreate,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> ClassMatterAssignment:
    """
    Assign a teacher to teach a specific matter in this class.

    Each class can have only one teacher per matter.
    """
    # Verify class exists
    stmt = select(SchoolClass).where(
        SchoolClass.id == class_id, SchoolClass.workspace_id == workspace.id
    )
    school_class = db.scalars(stmt).first()
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with id {class_id} not found"
        )

    # Verify matter exists
    stmt = select(Matter).where(
        Matter.id == assignment_data.matter_id, Matter.workspace_id == workspace.id
    )
    matter = db.scalars(stmt).first()
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matter with id {assignment_data.matter_id} not found",
        )

    # Verify teacher exists
    stmt = select(Teacher).where(
        Teacher.id == assignment_data.teacher_id, Teacher.workspace_id == workspace.id
    )
    teacher = db.scalars(stmt).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with id {assignment_data.teacher_id} not found",
        )

    # Check if matter is already assigned in this class
    stmt = select(ClassMatterAssignment).where(
        ClassMatterAssignment.class_id == class_id,
        ClassMatterAssignment.matter_id == assignment_data.matter_id,
        ClassMatterAssignment.workspace_id == workspace.id,
    )
    existing = db.scalars(stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Matter {matter.name} is already assigned in this class",
        )

    assignment = ClassMatterAssignment(
        workspace_id=workspace.id,
        class_id=class_id,
        matter_id=assignment_data.matter_id,
        teacher_id=assignment_data.teacher_id,
        hours_per_week=assignment_data.hours_per_week,
        requirements=assignment_data.requirements,
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
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> ClassMatterAssignment:
    """Update a class matter assignment (change teacher or hours)."""
    stmt = (
        select(ClassMatterAssignment)
        .where(
            ClassMatterAssignment.id == assignment_id,
            ClassMatterAssignment.class_id == class_id,
            ClassMatterAssignment.workspace_id == workspace.id,
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
            detail=f"Assignment with id {assignment_id} not found in class {class_id}",
        )

    if assignment_data.teacher_id is not None:
        # Verify new teacher exists
        stmt = select(Teacher).where(
            Teacher.id == assignment_data.teacher_id, Teacher.workspace_id == workspace.id
        )
        teacher = db.scalars(stmt).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Teacher with id {assignment_data.teacher_id} not found",
            )
        _validate_teacher_change_for_fixed_lessons(
            assignment, teacher.id, workspace.id, db
        )
        assignment.teacher_id = assignment_data.teacher_id

    if assignment_data.hours_per_week is not None:
        fixed_count = db.scalar(
            select(func.count())
            .select_from(FixedClassLesson)
            .where(
                FixedClassLesson.assignment_id == assignment.id,
                FixedClassLesson.workspace_id == workspace.id,
            )
        ) or 0
        if assignment_data.hours_per_week < fixed_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Weekly hours cannot be less than the number of fixed lessons "
                    f"({fixed_count})"
                ),
            )
        assignment.hours_per_week = assignment_data.hours_per_week

    if assignment_data.requirements is not None:
        assignment.requirements = assignment_data.requirements

    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/{class_id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class_assignment(
    class_id: int,
    assignment_id: int,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> None:
    """Remove a matter-teacher assignment from a class."""
    stmt = select(ClassMatterAssignment).where(
        ClassMatterAssignment.id == assignment_id,
        ClassMatterAssignment.class_id == class_id,
        ClassMatterAssignment.workspace_id == workspace.id,
    )
    assignment = db.scalars(stmt).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment with id {assignment_id} not found in class {class_id}",
        )

    fixed_lessons = db.scalars(
        select(FixedClassLesson).where(
            FixedClassLesson.assignment_id == assignment.id,
            FixedClassLesson.workspace_id == workspace.id,
        )
    ).all()
    for fixed_lesson in fixed_lessons:
        db.delete(fixed_lesson)
    db.delete(assignment)
    db.commit()
