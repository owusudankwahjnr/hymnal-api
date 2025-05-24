# app/models/verse.py

from sqlalchemy import Column, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Verse(Base):
    id = Column(Integer, primary_key=True, index=True)
    hymn_id = Column(Integer, ForeignKey("hymn.id"))
    order = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    hymn = relationship("Hymn", back_populates="verses")

    __table_args__ = (UniqueConstraint("hymn_id", "order", name="unique_verse_order_per_hymn"),)
