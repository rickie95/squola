"""Subject Matters API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from squola.database import get_db
from squola.models import Matter
from squola.schemas import (
    MatterCreate,
    MatterUpdate,
    MatterResponse,
    MatterWithTeachersResponse,
)

router = APIRouter(prefix="/matters", tags=["matters"])


@router.get("", response_model=list[MatterResponse])
def list_matters(db: Session = Depends(get_db)) -> list[MatterResponse]:
    """List all subject matters."""
    stmt = select(Matter)
    res: list[Matter] = list(db.scalars(stmt).all())
    results = [MatterResponse(id=r.id, name=r.name, default_requirements=r.default_requirements) for r in res]
    return results


@router.get("/{matter_id}", response_model=MatterWithTeachersResponse)
def get_matter(matter_id: int, db: Session = Depends(get_db)) -> Matter:
    """Get a specific matter by ID with its teachers."""
    stmt = (
        select(Matter)
        .where(Matter.id == matter_id)
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
def create_matter(matter_data: MatterCreate, db: Session = Depends(get_db)) -> Matter:
    """Create a new subject matter."""
    # Check if matter with same name already exists
    stmt = select(Matter).where(Matter.name == matter_data.name)
    existing = db.scalars(stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Matter '{matter_data.name}' already exists"
        )
    
    matter = Matter(
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
    db: Session = Depends(get_db)
) -> Matter:
    """Update an existing matter."""
    stmt = select(Matter).where(Matter.id == matter_id)
    matter = db.scalars(stmt).first()
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matter with id {matter_id} not found"
        )
    
    if matter_data.name is not None:
        # Check for name conflicts
        stmt = select(Matter).where(
            Matter.name == matter_data.name,
            Matter.id != matter_id,
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
    
    db.commit()
    db.refresh(matter)
    return matter


@router.delete("/{matter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_matter(matter_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a subject matter."""
    stmt = select(Matter).where(Matter.id == matter_id)
    matter = db.scalars(stmt).first()
    if not matter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matter with id {matter_id} not found"
        )
    
    db.delete(matter)
    db.commit()
