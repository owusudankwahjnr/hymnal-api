from sqlalchemy.orm import Session
from app.models.mapping import HymnMapping
from app.schemas.mapping import HymnMappingCreate, HymnMappingUpdate
from typing import List


def get(db: Session, mapping_id: int) -> HymnMapping | None:
    return db.query(HymnMapping).filter(HymnMapping.id == mapping_id).first()


def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[HymnMapping]:
    return db.query(HymnMapping).offset(skip).limit(limit).all()


def get_by_source_hymn(db: Session, source_hymn_id: int) -> List[HymnMapping]:
    return db.query(HymnMapping).filter(
        (HymnMapping.source_hymn_id == source_hymn_id) |
        (HymnMapping.target_hymn_id == source_hymn_id)
    ).all()


def create(db: Session, obj_in: HymnMappingCreate) -> HymnMapping:
    # Enforce source_id < target_id to support symmetry
    data = obj_in.model_dump()
    if data["source_hymn_id"] > data["target_hymn_id"]:
        data["source_hymn_id"], data["target_hymn_id"] = data["target_hymn_id"], data["source_hymn_id"]

    db_obj = HymnMapping(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, db_obj: HymnMapping, obj_in: HymnMappingUpdate) -> HymnMapping:
    for field, value in obj_in.model_dump(exclude_unset=True).items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete(db: Session, db_obj: HymnMapping):
    db.delete(db_obj)
    db.commit()
