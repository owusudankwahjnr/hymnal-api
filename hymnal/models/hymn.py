import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.models.base import Base


def generate_uuid():
    return str(uuid.uuid4())

class Hymn(Base):
    __tablename__ = "hymns"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    hymn_book_id = Column(String, ForeignKey("hymn_books.id"))
    title = Column(String, index=True)
    number = Column(Integer, index=True)
    variant_key = Column(String, nullable=True, index=True)
    content = Column(JSON)  # e.g., {"verses": [{"verse_tag": "v1", "verse_name": "Verse 1", "verse_content": "Text"}], "chorus": "Chorus"}
    hymn_book = relationship("HymnBook", back_populates="hymns")