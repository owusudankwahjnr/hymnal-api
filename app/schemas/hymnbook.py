from pydantic import BaseModel

class HymnBookBase(BaseModel):
    name: str

class HymnBookCreate(HymnBookBase):
    pass

class HymnBookUpdate(HymnBookBase):
    pass

class HymnBookOut(HymnBookBase):
    id: int

    class Config:
        from_attributes = True
