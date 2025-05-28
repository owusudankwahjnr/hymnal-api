# app/models/hymnbook.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class HymnBook(Base):
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    hymns = relationship("Hymn", back_populates="book", cascade="all, delete-orphan")
