import asyncio
import os
import sys
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Adjust path if script is run from root
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.database import AsyncSessionLocal  # your AsyncSessionLocal or session factory
from core.services.auth import get_password_hash
from user_management.models.user import User

async def create_superuser():
    print("\n🚀 FastAPI Superuser Creation\n" + "-" * 35)

    # Collect input from user
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = getpass("Password: ").strip()
    confirm = getpass("Confirm Password: ").strip()

    if password != confirm:
        print("❌ Passwords do not match.")
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).filter(User.username == username))
        if result.scalars().first():
            print(f"⚠️  User '{username}' already exists.")
            return

        hashed_password = get_password_hash(password)

        super_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_super_user=True,
            is_admin=True,
            is_active=True,
        )

        db.add(super_user)
        await db.commit()

        print(f"\n✅ Superuser '{username}' created successfully!")
        print(f"📧 Email: {email}")
        print(f"🦸 Superuser ID: {super_user.id}\n")

if __name__ == "__main__":
    try:
        asyncio.run(create_superuser())
    except KeyboardInterrupt:
        print("\nCancelled.")
