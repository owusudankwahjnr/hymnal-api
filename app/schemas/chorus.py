from pydantic import BaseModel, field_validator

class ChorusBase(BaseModel):
    text: str

class ChorusCreate(ChorusBase):

    @field_validator("text")
    def text_min_length(cls, v):
        if len(v.strip()) < 5:
            raise ValueError("Chorus text must be at least 5 characters long")
        return v

class ChorusUpdate(ChorusCreate):
    pass

class ChorusOut(ChorusBase):
    id: int

    class Config:
        from_attributes = True
