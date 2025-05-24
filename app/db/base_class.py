# app/db/base_class.py

from sqlalchemy.ext.declarative import as_declarative, declared_attr

@as_declarative()
class Base:
    id: int
    __name__: str

    # Automatically generate __tablename__ if not defined
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
