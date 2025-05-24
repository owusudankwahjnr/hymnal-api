from typing import List, Optional
from pydantic import BaseModel
from app.schemas.verse import VerseOut
from app.schemas.chorus import ChorusOut
from pydantic import field_validator

class HymnBase(BaseModel):
    number: int
    title: str
    hymn_book_id: int

class HymnCreate(HymnBase):
    verses: List[VerseOut]
    chorus: Optional[ChorusOut] = None

    @field_validator("number")
    def number_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Hymn number must be positive")
        return v

class HymnUpdate(BaseModel):
    number: Optional[int] = None
    title: Optional[str] = None
    hymn_book_id: Optional[int] = None
    verses: Optional[List[VerseOut]] = None
    chorus: Optional[ChorusOut] = None


class HymnOut(HymnBase):
    id: int
    verses: List[VerseOut]
    chorus: Optional[ChorusOut]

    class Config:
        from_attributes = True


class HymnSlide(BaseModel):
    title: str
    number: int
    verses: list[str]
    chorus: str | None = None