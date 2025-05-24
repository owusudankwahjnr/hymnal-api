from sqlalchemy.orm import Session
from app.models.hymnbook import HymnBook
from app.schemas.hymnbook import HymnBookCreate, HymnBookUpdate

def get(db: Session, id: int) -> HymnBook | None:
    return db.query(HymnBook).filter(HymnBook.id == id).first()

def get_all(db: Session, skip: int = 0, limit: int = 100):
    return db.query(HymnBook).offset(skip).limit(limit).all()

def create(db: Session, obj_in: HymnBookCreate) -> HymnBook:
    db_obj = HymnBook(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update(db: Session, db_obj: HymnBook, obj_in: HymnBookUpdate) -> HymnBook:
    for field, value in obj_in.dict(exclude_unset=True).items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete(db: Session, db_obj: HymnBook):
    db.delete(db_obj)
    db.commit()
