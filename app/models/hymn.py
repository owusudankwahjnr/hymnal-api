# app/models/hymn.py

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Hymn(Base):
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, index=True)
    title = Column(String, index=True)
    hymn_book_id = Column(Integer, ForeignKey("hymnbook.id"))

    book = relationship("HymnBook", back_populates="hymns")
    verses = relationship("Verse", back_populates="hymn", cascade="all, delete-orphan")
    chorus = relationship("Chorus", uselist=False, back_populates="hymn", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("number", "hymn_book_id", name="unique_hymn_in_book"),)
