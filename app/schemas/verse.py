from pydantic import BaseModel, field_validator

class VerseBase(BaseModel):
    order: int
    text: str

class VerseCreate(VerseBase):
    @field_validator("text")
    def text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Verse text must not be empty")
        return v

class VerseUpdate(VerseCreate):
    pass

class VerseOut(VerseBase):
    id: int

    class Config:
        from_attributes = True
