from pydantic import BaseModel
from typing import Optional, List

class HymnMappingBase(BaseModel):
    target_hymn_id: int
    relation_type: str = "semantic"
    note: Optional[str] = None

class HymnMappingCreate(HymnMappingBase):
    source_hymn_id: int

class HymnMappingUpdate(BaseModel):
    relation_type: Optional[str] = None
    note: Optional[str] = None

class HymnMappingOut(HymnMappingBase):
    id: int
    source_hymn_id: int

    class Config:
        from_attributes = True


class HymnMappingGroup(BaseModel):
    source_hymn_id: int
    mappings: List[HymnMappingOut]
