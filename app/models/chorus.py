# app/models/chorus.py

from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Chorus(Base):
    id = Column(Integer, primary_key=True, index=True)
    hymn_id = Column(Integer, ForeignKey("hymn.id"), unique=True)
    text = Column(Text, nullable=False)

    hymn = relationship("Hymn", back_populates="chorus")
