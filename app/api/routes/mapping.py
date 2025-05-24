from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud
from app.api.deps import get_db, get_current_user, require_admin
from app.models.user import User
from app.schemas.mapping import HymnMappingOut, HymnMappingCreate, HymnMappingUpdate

router = APIRouter(prefix="/mappings", tags=["Hymn Mappings"])

@router.get("/", response_model=List[HymnMappingOut])
def read_mappings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.mapping.get_all(db, skip=skip, limit=limit)

@router.get("/source/{source_hymn_id}", response_model=List[HymnMappingOut])
def read_by_source(source_hymn_id: int, db: Session = Depends(get_db)):
    return crud.mapping.get_by_source_hymn(db, source_hymn_id)

@router.post("/", response_model=HymnMappingOut, status_code=status.HTTP_201_CREATED)
def create_mapping(
    mapping_in: HymnMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return crud.mapping.create(db=db, obj_in=mapping_in)

@router.put("/{mapping_id}", response_model=HymnMappingOut)
def update_mapping(
    mapping_id: int,
    mapping_in: HymnMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    mapping = crud.mapping.get(db, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return crud.mapping.update(db=db, db_obj=mapping, obj_in=mapping_in)

@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mapping(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    mapping = crud.mapping.get(db, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    crud.mapping.delete(db=db, db_obj=mapping)
