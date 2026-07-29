from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


async def get_user_by_name(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.name == username))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def update_user_password(
    session: AsyncSession,
    user: User,
    hashed_password: str,
) -> User:
    user.hashed_password = hashed_password
    user.auth_version += 1
    await session.commit()
    await session.refresh(user)
    return user
