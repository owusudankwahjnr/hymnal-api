from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from app import crud
from app.api.deps import get_db, require_admin
from app.schemas.hymn import HymnOut, HymnCreate, HymnUpdate, HymnSlide
from app.models.user import User
from app.models.hymn import Hymn
from app.api.deps import get_current_user

router = APIRouter(prefix="/hymns", tags=["Hymns"])

@router.get("/", response_model=List[HymnOut], summary="List all hymns", description="Returns paginated list of hymns")
def read_hymns(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.hymn.get_all(db, skip=skip, limit=limit)

@router.post("/", response_model=HymnOut, status_code=status.HTTP_201_CREATED, summary="Create a new hymn",
    description="Only staff or superusers can add new hymns. A hymn must include at least one verse and may optionally include a chorus.")
def create_hymn(
    hymn_in: HymnCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return crud.hymn.create(db=db, obj_in=hymn_in)


@router.get(
    "/book/{hymnbook_id}",
    response_model=List[HymnOut],
    summary="List hymns from a specific hymn book",
    description="Retrieve all hymns that belong to a given hymn book by its ID."
)
def get_hymns_by_book(
    hymnbook_id: int,
    db: Session = Depends(get_db),
):
    return crud.hymn.get_by_hymnbook_id(db=db, hymnbook_id=hymnbook_id)

@router.get(
    "/book/{hymnbook_id}/search",
    response_model=List[HymnOut],
    summary="Search hymns by title in a hymn book",
    description="Search for hymns by partial or full title within a specific hymn book."
)
def search_hymns_in_book(
    hymnbook_id: int,
    query: str,
    db: Session = Depends(get_db),
):
    return crud.hymn.search_by_title_in_book(db=db, hymnbook_id=hymnbook_id, title=query)

@router.get("/book/{hymnbook_id}/slides", response_model=List[HymnSlide], summary="Slideshow hymns for mobile app")
def get_slides_by_book(hymnbook_id: int, db: Session = Depends(get_db)):
    return crud.hymn.get_hymn_slides_by_book(db, hymnbook_id)


@router.get(
    "/{hymn_id}/slide",
    response_model=HymnSlide,
    summary="Get a hymn by ID (slide format)",
    description="Returns a hymn in a slide-ready format with just text fields"
)
def get_hymn_slide(
    hymn_id: int,
    db: Session = Depends(get_db)
):
    slide = crud.hymn.get_hymn_slide_by_id(db=db, hymn_id=hymn_id)
    if not slide:
        raise HTTPException(status_code=404, detail="Hymn not found")
    return slide


@router.get("/book/{hymnbook_id}/paged", response_model=List[HymnSlide], summary="Slideshow hymns for mobile app return paginated results")
def get_hymns_paged(
    hymnbook_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return crud.hymn.get_hymn_slides_by_book(db, hymnbook_id)[skip: skip + limit]



@router.get("/search-by-title/", response_model=List[HymnOut], summary="Search hymns by title", description="Search hymns by title and return paginated results")
def search_hymns_by_title(
    title: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    results = crud.hymn.search_by_title(db=db, title=title, skip=skip, limit=limit)
    if not results:
        raise HTTPException(status_code=404, detail="No hymns found matching the title")
    return results



@router.get("/{hymn_id}", response_model=HymnOut, summary="Get a hymn by ID",
    description="Retrieve a specific hymn by its unique ID.")
def read_hymn(hymn_id: int, db: Session = Depends(get_db)):
    hymn = crud.hymn.get(db, hymn_id)
    if not hymn:
        raise HTTPException(status_code=404, detail="Hymn not found")
    return hymn



@router.put("/{hymn_id}", response_model=HymnOut, summary="Update a hymn",
    description="Only staff or superusers can update existing hymns.")
def update_hymn(
    hymn_id: int,
    hymn_in: HymnUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):

    hymn = crud.hymn.get(db, hymn_id)
    if not hymn:
        raise HTTPException(status_code=404, detail="Hymn not found")
    return crud.hymn.update(db=db, db_obj=hymn, obj_in=hymn_in)


@router.delete("/{hymn_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a hymn",
    description="Only staff or superusers can delete hymns. This will also delete associated verses and chorus.")
def delete_hymn(
        hymn_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):

    hymn = crud.hymn.get(db, hymn_id)
    if not hymn:
        raise HTTPException(status_code=404, detail="Hymn not found")
    crud.hymn.delete(db=db, db_obj=hymn)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
