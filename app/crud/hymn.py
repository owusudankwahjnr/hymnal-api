from sqlalchemy.orm import Session
from app.models.hymn import Hymn
from app.models.verse import Verse
from app.models.chorus import Chorus
from app.schemas.hymn import HymnCreate, HymnUpdate
from typing import List

def get(db: Session, id: int) -> Hymn | None:
    return db.query(Hymn).filter(Hymn.id == id).first()


def get_all(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Hymn).offset(skip).limit(limit).all()

def search_by_title(db: Session, title: str, skip: int = 0, limit: int = 100) -> list[Hymn]:
    return (db.query(Hymn).filter(Hymn.title.ilike(f"%{title}%")).offset(skip).limit(limit).all())

def create(db: Session, obj_in: HymnCreate) -> Hymn:
    hymn = Hymn(
        number=obj_in.number,
        title=obj_in.title,
        hymn_book_id=obj_in.hymn_book_id,
    )
    db.add(hymn)
    db.flush()  # assign hymn.id before adding verses or chorus

    for verse_data in obj_in.verses:
        verse = Verse(
            hymn_id=hymn.id,
            order=verse_data.order,
            text=verse_data.text
        )
        db.add(verse)

    if obj_in.chorus:
        chorus = Chorus(
            hymn_id=hymn.id,
            text=obj_in.chorus.text
        )
        db.add(chorus)

    db.commit()
    db.refresh(hymn)
    return hymn


def update(db: Session, db_obj: Hymn, obj_in: HymnUpdate) -> Hymn:
    for field, value in obj_in.model_dump(exclude_unset=True).items():
        if field in ["verses", "chorus"]:
            continue  # Handle nested objects separately
        setattr(db_obj, field, value)

    # Update verses if provided
    if obj_in.verses is not None:
        db.query(Verse).filter(Verse.hymn_id == db_obj.id).delete()
        for verse_data in obj_in.verses:
            verse = Verse(
                hymn_id=db_obj.id,
                order=verse_data.order,
                text=verse_data.text
            )
            db.add(verse)

    # Update chorus
    if obj_in.chorus is not None:
        existing_chorus = db.query(Chorus).filter(Chorus.hymn_id == db_obj.id).first()
        if existing_chorus:
            existing_chorus.text = obj_in.chorus.text
        else:
            chorus = Chorus(hymn_id=db_obj.id, text=obj_in.chorus.text)
            db.add(chorus)

    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete(db: Session, db_obj: Hymn):
    db.delete(db_obj)
    db.commit()


def get_by_hymnbook_id(db: Session, hymnbook_id: int) -> List[Hymn]:
    return db.query(Hymn).filter(Hymn.hymn_book_id == hymnbook_id).all()

def search_by_title_in_book(db: Session, hymnbook_id: int, title: str) -> List[Hymn]:
    return db.query(Hymn).filter(
        Hymn.hymn_book_id == hymnbook_id,
        Hymn.title.ilike(f"%{title}%")
    ).all()



def get_hymn_slides_by_book(db: Session, hymnbook_id: int):
    hymns = db.query(Hymn).filter(Hymn.hymn_book_id == hymnbook_id).all()
    slides = []
    for hymn in hymns:
        verses = [verse.text for verse in hymn.verses]
        chorus = hymn.chorus.text if hymn.chorus else None
        slides.append({
            "title": hymn.title,
            "number": hymn.number,
            "verses": verses,
            "chorus": chorus
        })
    return slides

# app/crud/hymn.py
def get_hymn_slide_by_id(db: Session, hymn_id: int) -> dict | None:
    hymn = db.query(Hymn).filter(Hymn.id == hymn_id).first()
    if not hymn:
        return None
    return {
        "title": hymn.title,
        "number": hymn.number,
        "verses": [v.text for v in hymn.verses],
        "chorus": hymn.chorus.text if hymn.chorus else None
    }
