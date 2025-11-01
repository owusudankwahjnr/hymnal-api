# user_management/models/role.py
import uuid
from sqlalchemy import Column, Integer, String, ForeignKey
from core.models.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class Role(Base):
    __tablename__ = "roles"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)

class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    role_id = Column(String, ForeignKey("roles.id"), primary_key=True)


