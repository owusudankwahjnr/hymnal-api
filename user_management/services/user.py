from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, UploadFile
from user_management.models.user import User
from user_management.models.audit_log import AuditLog
from user_management.models.role import Role, UserRole
from user_management.models.permission import Permission, RolePermission
from user_management.schemas.user import UserCreate, UserUpdate, UserOut
from core.services.auth import get_password_hash, verify_password
import pyotp
import aiofiles
import os
import uuid
from datetime import datetime

# Base directory for user images
USER_IMAGE_DIR = "media/users/images"

# Ensure directory exists (synchronous, run at startup)
os.makedirs(USER_IMAGE_DIR, exist_ok=True)


async def create_user(db: AsyncSession, user: UserCreate, current_user_id: str = None) -> User:
    async with db.begin():
        result = await db.execute(select(User).filter(User.username == user.username, User.is_active == True))
        db_user = result.scalars().first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        result = await db.execute(select(User).filter(User.email == user.email, User.is_active == True))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed_password = get_password_hash(user.password) if user.password else None
        db_user = User(
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            other_name=user.other_name,
            hashed_password=hashed_password,
            is_admin=user.is_admin,
            is_super_user=user.is_super_user
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        await log_action(db, current_user_id or db_user.id, "CREATE_USER",
                         f"Created user {user.username}, is_super_user={user.is_super_user}")
        return db_user


async def get_user_by_username(db: AsyncSession, username: str) -> User:
    result = await db.execute(select(User).filter(User.username == username, User.is_active == True))
    return result.scalars().first()


async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate, current_user: UserOut) -> User:
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == user_id, User.is_active == True))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user_update.is_super_user is not None and not current_user.is_super_user:
            raise HTTPException(status_code=403, detail="Only superusers can modify superuser status")
        for key, value in user_update.dict(exclude_unset=True).items():
            setattr(user, key, value)
        await db.commit()
        await db.refresh(user)
        await log_action(db, current_user.id, "UPDATE_USER",
                         f"Updated user {user.username}, is_super_user={user.is_super_user}")
        return user


async def update_user_image(db: AsyncSession, user_id: str, image: UploadFile, current_user_id: str) -> User:
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == user_id, User.is_active == True))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if image.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Generate unique filename
        file_extension = image.filename.split(".")[-1]
        filename = f"user_{user_id}_{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(USER_IMAGE_DIR, filename)

        # Save file asynchronously
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(await image.read())

        # Delete old image if exists
        if user.image_path and os.path.exists(user.image_path):
            os.remove(user.image_path)  # Synchronous, as aiofiles.delete is not critical

        # Update path
        user.image_path = file_path
        await db.commit()
        await db.refresh(user)
        await log_action(db, current_user_id, "UPDATE_USER_IMAGE", f"Updated image for user {user.username}")
        return user


async def soft_delete_user(db: AsyncSession, user_id: str, current_user_id: str) -> User:
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == user_id, User.is_active == True))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.is_super_user:
            raise HTTPException(status_code=403, detail="Cannot delete superuser")
        user.is_active = False
        user.deleted_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        await log_action(db, current_user_id, "DELETE_USER", f"Soft-deleted user {user.username}")
        return user


async def setup_2fa(db: AsyncSession, user_id: str, current_user_id: str) -> str:
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == user_id, User.is_active == True))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        totp_secret = pyotp.random_base32()
        user.totp_secret = totp_secret
        await db.commit()
        await db.refresh(user)
        await log_action(db, current_user_id, "SETUP_2FA", f"Enabled 2FA for user {user.username}")
        return totp_secret


async def verify_2fa(db: AsyncSession, user: UserOut, token: str) -> bool:
    result = await db.execute(select(User).filter(User.id == user.id, User.is_active == True))
    db_user = result.scalars().first()
    if not db_user or not db_user.totp_secret:
        return False
    totp = pyotp.TOTP(db_user.totp_secret)
    return totp.verify(token)


async def create_role(db: AsyncSession, name: str, description: str = None, current_user_id: int = None) -> Role:
    async with db.begin():
        result = await db.execute(select(Role).filter(Role.name == name))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Role already exists")
        role = Role(name=name, description=description)
        db.add(role)
        await db.commit()
        await db.refresh(role)
        await log_action(db, current_user_id or 0, "CREATE_ROLE", f"Created role {name}")
        return role


async def create_permission(db: AsyncSession, name: str, description: str = None,
                            current_user_id: int = None) -> Permission:
    async with db.begin():
        result = await db.execute(select(Permission).filter(Permission.name == name))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Permission already exists")
        permission = Permission(name=name, description=description)
        db.add(permission)
        await db.commit()
        await db.refresh(permission)
        await log_action(db, current_user_id or 0, "CREATE_PERMISSION", f"Created permission {name}")
        return permission


async def assign_role_to_user(db: AsyncSession, user_id: str, role_id: str, current_user_id: str):
    async with db.begin():
        result = await db.execute(select(User).filter(User.id == user_id, User.is_active == True))
        user = result.scalars().first()
        result = await db.execute(select(Role).filter(Role.id == role_id))
        role = result.scalars().first()
        if not user or not role:
            raise HTTPException(status_code=404, detail="User or role not found")
        result = await db.execute(select(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == role_id))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Role already assigned to user")
        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.add(user_role)
        await db.commit()
        await log_action(db, current_user_id, "ASSIGN_ROLE", f"Assigned role {role_id} to user {user_id}")


async def assign_permission_to_role(db: AsyncSession, role_id: str, permission_id: str, current_user_id: str):
    async with db.begin():
        result = await db.execute(select(Role).filter(Role.id == role_id))
        role = result.scalars().first()
        result = await db.execute(select(Permission).filter(Permission.id == permission_id))
        permission = result.scalars().first()
        if not role or not permission:
            raise HTTPException(status_code=404, detail="Role or permission not found")
        result = await db.execute(select(RolePermission).filter(RolePermission.role_id == role_id,
                                                                RolePermission.permission_id == permission_id))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Permission already assigned to role")
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        db.add(role_permission)
        await db.commit()
        await log_action(db, current_user_id, "ASSIGN_PERMISSION",
                         f"Assigned permission {permission_id} to role {role_id}")


async def log_action(db: AsyncSession, user_id: str, action: str, details: str = None):
    audit_log = AuditLog(user_id=user_id, action=action, details=details, timestamp=datetime.utcnow())
    db.add(audit_log)
    await db.commit()