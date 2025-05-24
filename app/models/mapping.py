# app/models/mapping.py

from sqlalchemy import Column, Integer, ForeignKey, String, Text, UniqueConstraint,event
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class HymnMapping(Base):
    __tablename__ = "hymn_mapping"

    id = Column(Integer, primary_key=True, index=True)

    # When a referenced hymn is deleted, delete the mapping automatically
    source_hymn_id = Column(Integer, ForeignKey("hymn.id", ondelete="CASCADE"), nullable=False, index=True)
    target_hymn_id = Column(Integer, ForeignKey("hymn.id", ondelete="CASCADE"), nullable=False, index=True)

    # Type of relationship e.g. "translation", "thematic", "alternate_version"
    relation_type = Column(String, default="semantic", nullable=False)

    # Optional notes about the mapping
    note = Column(Text, nullable=True)

    # ORM relationships for easy access
    source_hymn = relationship("Hymn", foreign_keys=[source_hymn_id], backref="source_mappings", passive_deletes=True)
    target_hymn = relationship("Hymn", foreign_keys=[target_hymn_id], backref="target_mappings", passive_deletes=True)

    __table_args__ = (
        # Enforce unique constraint regardless of A→B or B→A
        UniqueConstraint('source_hymn_id', 'target_hymn_id', name="unique_hymn_mapping"),
    )

# Automatically swap source/target to maintain source_id < target_id
@event.listens_for(HymnMapping, "before_insert")
def enforce_order(mapper, connection, target: HymnMapping):
    if target.source_hymn_id > target.target_hymn_id:
        target.source_hymn_id, target.target_hymn_id = target.target_hymn_id, target.source_hymn_id
