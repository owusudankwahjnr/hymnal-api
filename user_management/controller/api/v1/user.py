from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from user_management.schemas.user import UserCreate, UserUpdate, UserOut, Token
from user_management.services.user import (
    create_user, get_user_by_username, update_user, update_user_image,
    soft_delete_user, setup_2fa, verify_2fa, assign_role_to_user,
    assign_permission_to_role, create_role, create_permission
)
from core.dependencies import get_db, check_permission
from core.services.auth import create_access_token, verify_password, get_current_user

router = APIRouter(prefix="/api/v1/user_management", tags=["User Management"])

@router.post(
    "/register",
    response_model=UserOut,
    summary="Register a new user",
    description="""
    Register a new user in the system.
- **user**: User creation details (username, email, password, etc.).
- Requires authentication and `create_user` permission.
- Superusers can set `is_super_user=true`; others cannot.
    """,
    response_description="The created user object",
)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("create_user"))
):
    if user.is_super_user and not current_user.is_super_user:
        raise HTTPException(status_code=403, detail="Only superusers can create superusers")
    return await create_user(db, user, current_user.id)

@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="""
    Authenticate a user and issue a JWT token.
- **form_data**: Username and password.
- Returns a bearer token valid for 30 minutes.
- If 2FA is enabled, verification may be required (currently optional).
    """,
    response_description="JWT token for authenticated user",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.totp_secret:
        # TODO: Enforce 2FA verification in production
        pass
    access_token = create_access_token(data={"sub": user.username, "is_super_user": user.is_super_user})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post(
    "/2fa/setup",
    response_model=str,
    summary="Set up 2FA for a user",
    description="""
    Set up two-factor authentication for the authenticated user.
- Returns a TOTP secret to be used with an authenticator app.
- Requires authentication and `setup_2fa` permission.
    """,
    response_description="TOTP secret for 2FA setup",
)
async def setup_2fa_endpoint(
    current_user: UserOut = Depends(check_permission("setup_2fa")),
    db: AsyncSession = Depends(get_db)
):
    totp_secret = await setup_2fa(db, current_user.id, current_user.id)
    if not totp_secret:
        raise HTTPException(status_code=404, detail="User not found")
    return totp_secret

@router.post(
    "/2fa/verify",
    summary="Verify 2FA token",
    description="""
    Verify a TOTP token for the authenticated user.
- **token**: The 6-digit TOTP code from an authenticator app.
- Requires authentication and `verify_2fa` permission.
    """,
    response_description="Confirmation of successful 2FA verification",
)
async def verify_2fa_endpoint(
    token: str,
    current_user: UserOut = Depends(check_permission("verify_2fa")),
    db: AsyncSession = Depends(get_db)
):
    if not await verify_2fa(db, current_user, token):
        raise HTTPException(status_code=400, detail="Invalid 2FA token")
    return {"detail": "2FA verified"}

@router.put(
    "/users/{user_id}",
    response_model=UserOut,
    summary="Update a user",
    description="""
    Update an existing user's details.
- **user_id**: The ID of the user to update.
- **user_update**: Updated user details (e.g., email, first_name, is_super_user).
- Only superusers can change `is_super_user`.
- Requires authentication and `update_user` permission.
    """,
    response_description="The updated user object",
)
async def update_user_endpoint(
    user_id: int,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("update_user"))
):
    updated_user = await update_user(db, user_id, user_update, current_user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.post(
    "/users/{user_id}/image",
    summary="Upload user profile image",
    description="""
    Upload a profile image for a user.
- **user_id**: The ID of the user.
- **image**: The image file (must be JPEG or PNG).
- Requires authentication and `update_user` permission.
    """,
    response_description="Confirmation of successful image upload",
)
async def upload_user_image(
    user_id: int,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("update_user"))
):
    updated_user = await update_user_image(db, user_id, image, current_user.id)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "Image uploaded"}

@router.delete(
    "/users/{user_id}",
    summary="Soft delete a user",
    description="""
    Soft delete a user by setting is_active to false.
- **user_id**: The ID of the user to delete.
- Superusers are protected from deletion.
- Requires authentication and `delete_user` permission.
    """,
    response_description="Confirmation of successful deletion",
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("delete_user"))
):
    user = await soft_delete_user(db, user_id, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted"}

@router.post(
    "/roles",
    response_model=dict,
    summary="Create a new role",
    description="""
    Create a new role for the RBAC system.
- **name**: Unique name of the role (e.g., 'editor').
- **description**: Optional description of the role.
- Requires authentication and `create_role` permission.
    """,
    response_description="The created role",
)
async def create_role_api(
    name: str,
    description: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("create_role"))
):
    role = await create_role(db, name, description, current_user.id)
    return {"id": role.id, "name": role.name, "description": role.description}

@router.post(
    "/permissions",
    response_model=dict,
    summary="Create a new permission",
    description="""
    Create a new permission for the RBAC system.
- **name**: Unique name of the permission (e.g., 'edit_hymn').
- **description**: Optional description of the permission.
- Requires authentication and `create_permission` permission.
    """,
    response_description="The created permission",
)
async def create_permission_api(
    name: str,
    description: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("create_permission"))
):
    permission = await create_permission(db, name, description, current_user.id)
    return {"id": permission.id, "name": permission.name, "description": permission.description}

@router.post(
    "/users/{user_id}/roles/{role_id}",
    summary="Assign a role to a user",
    description="""
    Assign a role to a user.
- **user_id**: The ID of the user.
- **role_id**: The ID of the role to assign.
- Requires authentication and `assign_role` permission.
    """,
    response_description="Confirmation of role assignment",
)
async def assign_role(
    user_id: str,
    role_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("assign_role"))
):
    await assign_role_to_user(db, user_id, role_id, current_user.id)
    return {"detail": "Role assigned"}

@router.post(
    "/roles/{role_id}/permissions/{permission_id}",
    summary="Assign a permission to a role",
    description="""
    Assign a permission to a role for RBAC.
- **role_id**: The ID of the role.
- **permission_id**: The ID of the permission to assign.
- Requires authentication and `assign_permission` permission.
    """,
    response_description="Confirmation of permission assignment",
)
async def assign_permission(
    role_id: str,
    permission_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(check_permission("assign_permission"))
):
    await assign_permission_to_role(db, role_id, permission_id, current_user.id)
    return {"detail": "Permission assigned"}