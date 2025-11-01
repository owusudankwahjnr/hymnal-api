from pydantic import BaseModel, field_validator
from typing import Optional, Dict

class Verse(BaseModel):
    verse_tag: str  # e.g., "v1", "intro" for ordering
    verse_name: str  # e.g., "Verse 1", "Opening" for display
    verse_content: str  # Text of the verse

class HymnBookBase(BaseModel):
    title: str

class HymnBookCreate(HymnBookBase):
    pass

class HymnBookUpdate(BaseModel):
    title: Optional[str] = None
    thumbnail_path: Optional[str] = None  # e.g., "hymn_books/thumbnails/book_1.jpg"

class HymnBookOut(HymnBookBase):
    id: str
    thumbnail_path: Optional[str] = None
    class Config:
        from_attributes = True

class HymnBase(BaseModel):
    title: str
    number: int
    content: Dict  # e.g., {"verses": [{"verse_tag": "v1", "verse_name": "Verse 1", "verse_content": "Text"}], "chorus": Optional[str]}
    variant_key: Optional[str] = None

    @field_validator("content")
    def validate_content(cls, v):
        if not v.get("verses") or not isinstance(v["verses"], list) or len(v["verses"]) < 1:
            raise ValueError("Hymn must have at least one verse")
        for verse in v["verses"]:
            if not all(key in verse for key in ["verse_tag", "verse_name", "verse_content"]):
                raise ValueError("Each verse must have verse_tag, verse_name, and verse_content")
        if "chorus" in v and not isinstance(v["chorus"], str):
            raise ValueError("Chorus must be a string")
        return v

class HymnCreate(HymnBase):
    hymn_book_id: str

class HymnUpdate(HymnBase):
    pass

class HymnOut(HymnBase):
    id: str
    hymn_book_id: str
    class Config:
        from_attributes = True

class HymnSearchResult(BaseModel):
    id: str
    title: str
    number: int
    hymn_book_id: str
    hymn_book_title: str
    variant_key: Optional[str] = None

class HymnVariantResult(HymnSearchResult):
    pass

class HymnFilterParams(BaseModel):
    title: Optional[str] = None
    number: Optional[int] = None
    hymn_book_id: Optional[str] = None
    skip: int = 0
    limit: int = 10