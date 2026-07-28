import logging
from typing import Optional
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Request, Response, Security, status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.users.crud import (
    confirm_user,
    create_user,
    find_user_by_email,
    get_user_by_id,
    get_user_from_db,
    update_user_db,
)
from src.api_v1.users.schemas import (
    LoginSchemas,
    OutUserSchemas,
    TokenSchemas,
    UserCreateSchemas,
    UserInfoSchemas,
    UserUpdatePartialSchemas,
    UserUpdateSchemas,
)
from src.core.config import COOKIE_NAME, api_key_header, configure_logging, setting
from src.core.database import get_async_session, get_redis_connection
from src.core.depends import (
    current_user_authorization,
    user_by_id,
)
from src.core.exceptions import (
    EmailInUse,
    ErrorInData,
    NotFindUser,
    UniqueViolationError,
)
from src.core.jwt_utils import create_jwt, decode_jwt, validate_password
from src.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


@router.get(
    "/register_confirm",
    status_code=status.HTTP_200_OK,
)
async def get_register_confirm(
    token: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Подтверждение регистрации пользователя через почту
    """
    try:
        await confirm_user(session=session, token=token)
    except ErrorInData:
        redirect_url = "https://airportcards.ru/?error=invalid_token"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse(url="https://airportcards.ru/?success=true", status_code=status.HTTP_302_FOUND)


@router.post("/login", response_model=OutUserSchemas, status_code=status.HTTP_202_ACCEPTED)
async def user_login(
    response: Response,
    request: Request,
    data_login: LoginSchemas,
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_connection),
) -> OutUserSchemas:
    """
    Логирование пользователя
    """
    logger.info(f"start login {data_login.username}")

    try:
        user: User = await get_user_from_db(session=session, email=data_login.username)
    except NotFindUser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The user with the username: {data_login.username} not found",
        )

    if await validate_password(password=data_login.password, hashed_password=user.hashed_password):
        access_token: str = await create_jwt(
            user=str(user.id),
            expire_minutes=setting.auth_jwt.access_token_expire_minutes,
        )
        refresh_token: str = await create_jwt(
            user=str(user.id),
            expire_minutes=setting.auth_jwt.refresh_token_expire_minutes,
        )

        response.set_cookie(
            key=COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=False,  # True в production
            samesite="lax",
            path="/",
        )

        request.session["user"] = {"family_name": user.full_name, "id": str(user.id)}
        await redis.set(str(user.id), refresh_token)

        logger.info(f"User {data_login.username} logged in")

        return OutUserSchemas(
            access_token=access_token,
            token_type="bearer",
            user=UserInfoSchemas(
                id=str(user.id),
                email=data_login.username,
                full_name=user.full_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
            ),
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error password for login: {data_login.username}",
        )



@router.get("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request, response: Response) -> None:
    """
    Обрабатывает выход пользователя из системы.
    """
    response.delete_cookie(COOKIE_NAME)
    request.session.clear()


@router.put("/{id_user}/", response_model=UserInfoSchemas, status_code=status.HTTP_200_OK)
async def update_user(
    user_update: UserUpdateSchemas,
    user: User = Depends(user_by_id),
    session: AsyncSession = Depends(get_async_session),
) -> UserInfoSchemas:
    """
    Переписывает данные пользователе
    """
    try:
        res = await update_user_db(session=session, user=user, user_update=user_update)
    except UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate email",
        )
    else:
        return UserInfoSchemas(**res.__dict__)


@router.patch("/{id_user}/", response_model=UserInfoSchemas, status_code=status.HTTP_200_OK)
async def update_user_partial(
    user_update: UserUpdatePartialSchemas,
    user: User = Depends(user_by_id),
    session: AsyncSession = Depends(get_async_session),
) -> UserInfoSchemas:
    """
    Редактирует данные пользователе
    """
    try:
        res = await update_user_db(session=session, user=user, user_update=user_update, partial=True)
    except UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate email",
        )
    else:
        return UserInfoSchemas(**res.__dict__)
