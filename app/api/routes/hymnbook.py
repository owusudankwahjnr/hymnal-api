from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from app import crud, models, schemas
from app.api import deps

router = APIRouter(prefix="/hymnbooks", tags=["HymnBooks"])


@router.get("/", response_model=List[schemas.HymnBookOut], summary="List all hymn books",
    description="Retrieve a list of all hymn books available in the system. Supports pagination with skip and limit.")
def list_hymnbooks(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return crud.hymnbook.get_all(db, skip=skip, limit=limit)


@router.post("/", response_model=schemas.HymnBookOut, summary="Create a hymn book",
    description="Only staff or superusers can add a new hymn book. Each name must be unique.")
def create_hymnbook(
        hymnbook_in: schemas.HymnBookCreate,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.require_admin),
):
    return crud.hymnbook.create(db, hymnbook_in)


@router.put("/{hymnbook_id}", response_model=schemas.HymnBookOut, summary="Update a hymn book",
    description="Update the name or details of a hymn book. Only staff or superusers can perform this action.")
def update_hymnbook(
        hymnbook_id: int,
        hymnbook_in: schemas.HymnBookUpdate,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.require_admin),
):
    hymnbook = crud.hymnbook.get(db, hymnbook_id)
    if not hymnbook:
        raise HTTPException(status_code=404, detail="Hymn book not found")

    return crud.hymnbook.update(db, hymnbook, hymnbook_in)


@router.delete("/{hymnbook_id}", summary="Delete a hymn book",
    description="Remove a hymn book from the system. Only allowed for staff or superusers.")
def delete_hymnbook(
        hymnbook_id: int,
        db: Session = Depends(deps.get_db),
        current_user: models.User = Depends(deps.require_admin),
):
    hymnbook = crud.hymnbook.get(db, hymnbook_id)
    if not hymnbook:
        raise HTTPException(status_code=404, detail="Hymn book not found")
    crud.hymnbook.delete(db, hymnbook)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
