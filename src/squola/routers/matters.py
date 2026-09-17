"""Subject Matters API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from squola.auth import get_current_workspace
from squola.database import get_db
from squola.scheduler import requirement_conflict
from squola.models import ClassMatterAssignment, Matter, Workspace
from squola.schemas import (
    MatterCreate,
    MatterUpdate,
    MatterResponse,
    MatterWithTeachersResponse,
)

router = APIRouter(prefix="/matters", tags=["matters"])


def _reject_impossible_defaults(requirements) -> None:
    """A matter's defaults are checked without weekly hours: it has none."""
    reason = requirement_conflict(requirements)
    if reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"These default requirements cannot be scheduled: {reason}",
        )


def _plan_default_requirement_propagation(
    matter: Matter,
    new_defaults,
    workspace_id: int,
    db: Session,
) -> dict[ClassMatterAssignment, list]:
    """
    Requirements each existing assignment of this matter should end up with.

    The defaults are applied as a delta rather than copied over: what the matter
    gained is added, what it lost is removed, and a requirement set on the
    assignment alone survives both. Raises 400, without planning anything, when
    the result would be impossible to schedule for any assignment.
    """
    if new_defaults is None:
        return {}

    _reject_impossible_defaults(new_defaults)

    old = set(matter.default_requirements or [])
    new = set(new_defaults)
    added, removed = new - old, old - new
    if not added and not removed:
        return {}

    stmt = select(ClassMatterAssignment).where(
        ClassMatterAssignment.matter_id == matter.id,
        ClassMatterAssignment.workspace_id == workspace_id,
    )

    propagation: dict[ClassMatterAssignment, list] = {}
    conflicts: list[str] = []
    for assignment in db.scalars(stmt):
        requirements = sorted((set(assignment.requirements or []) | added) - removed)
        reason = requirement_conflict(requirements, assignment.hours_per_week)
        if reason:
            conflicts.append(f"assignment {assignment.id} ({reason})")
        else:
            propagation[assignment] = requirements

    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "These default requirements cannot be scheduled for "
                + ", ".join(conflicts)
            ),
        )

    return propagation


@router.get("", response_model=list[MatterResponse])
def list_matters(
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> list[MatterResponse]:
    """List all subject matters."""
    stmt = select(Matter).where(Matter.workspace_id == workspace.id)
    res: list[Matter] = list(db.scalars(stmt).all())
    results = [MatterResponse(id=r.id, name=r.name, default_requirements=r.default_requirements) for r in res]
    return results


@router.get("/{matter_id}", response_model=MatterWithTeachersResponse)
def get_matter(
    matter_id: int,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> Matter:
    """Get a specific matter by ID with its teachers."""
    stmt = (
        select(Matter)
        .where(Matter.id == matter_id, Matter.workspace_id == workspace.id)
        .options(selectinload(Matter.teachers))
    )
    matter = db.scalars(stmt).first()
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matter with id {matter_id} not found"
        )
    return matter


@router.post("", response_model=MatterResponse, status_code=status.HTTP_201_CREATED)
def create_matter(
    matter_data: MatterCreate,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> Matter:
    """Create a new subject matter."""
    # Check if matter with same name already exists
    stmt = select(Matter).where(
        Matter.name == matter_data.name,
        Matter.workspace_id == workspace.id,
    )
    existing = db.scalars(stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Matter '{matter_data.name}' already exists"
        )
    
    _reject_impossible_defaults(matter_data.default_requirements)

    matter = Matter(
        workspace_id=workspace.id,
        name=matter_data.name,
        default_requirements=matter_data.default_requirements or []
    )
    db.add(matter)
    db.commit()
    db.refresh(matter)
    return matter


@router.put("/{matter_id}", response_model=MatterResponse)
def update_matter(
    matter_id: int,
    matter_data: MatterUpdate,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> Matter:
    """Update an existing matter."""
    stmt = select(Matter).where(Matter.id == matter_id, Matter.workspace_id == workspace.id)
    matter = db.scalars(stmt).first()
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matter with id {matter_id} not found"
        )
    
    # Work out the propagation before any field is mutated, so that a rejected
    # request leaves both the matter and its assignments untouched.
    propagation = _plan_default_requirement_propagation(
        matter, matter_data.default_requirements, workspace.id, db
    )

    if matter_data.name is not None:
        # Check for name conflicts
        stmt = select(Matter).where(
            Matter.name == matter_data.name,
            Matter.id != matter_id,
            Matter.workspace_id == workspace.id,
        )
        existing = db.scalars(stmt).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Matter '{matter_data.name}' already exists"
            )
        matter.name = matter_data.name
    
    if matter_data.default_requirements is not None:
        matter.default_requirements = matter_data.default_requirements

    for assignment, requirements in propagation.items():
        assignment.requirements = requirements

    db.commit()
    db.refresh(matter)
    return matter


@router.delete("/{matter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_matter(
    matter_id: int,
    db: Session = Depends(get_db),
    workspace: Workspace = Depends(get_current_workspace),
) -> None:
    """Delete a subject matter."""
    stmt = select(Matter).where(Matter.id == matter_id, Matter.workspace_id == workspace.id)
    matter = db.scalars(stmt).first()
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matter with id {matter_id} not found"
        )
    
    db.delete(matter)
    db.commit()
