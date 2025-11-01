# user_management/models/permission.py
import uuid

from sqlalchemy import Column, Integer, String, ForeignKey
from core.models.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)

class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id = Column(String, ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(String, ForeignKey("permissions.id"), primary_key=True)