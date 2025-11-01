import uuid

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from core.models.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class HymnBook(Base):
    __tablename__ = "hymn_books"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    title = Column(String, index=True)
    thumbnail_path = Column(String, nullable=True)  # e.g., "hymn_books/thumbnails/book_1.jpg"
    hymns = relationship("Hymn", back_populates="hymn_book")