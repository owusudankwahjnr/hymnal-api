from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import AsyncSessionLocal
from core.services.auth import get_current_user
from user_management.models.user import User
from user_management.models.permission import Permission, RolePermission
from user_management.models.role import Role, UserRole
from core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user_management/login")



def check_permission(permission: str):
    async def check_permission_inner(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
    ):
        user = await get_current_user(token, db)
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
        if user.is_super_user or user.is_admin:
            return user
        result = await db.execute(
            select(Permission)
            .join(RolePermission)
            .join(UserRole)
            .filter(UserRole.user_id == user.id, Permission.name == permission)
        )
        if not result.scalars().first():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return user
    return check_permission_inner