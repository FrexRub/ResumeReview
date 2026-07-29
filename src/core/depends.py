from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.users.crud import get_user_by_id
from src.core.database import get_async_session
from src.core.jwt_utils import decode_jwt
from src.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить авторизацию",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def current_user_authorization(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    try:
        payload = decode_jwt(token, expected_type="access")
        user_id = UUID(payload["sub"])
        auth_version = int(payload["auth_version"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise credentials_error() from exc

    user = await get_user_by_id(session, user_id)
    if user is None or not user.is_active or user.auth_version != auth_version:
        raise credentials_error()
    return user
