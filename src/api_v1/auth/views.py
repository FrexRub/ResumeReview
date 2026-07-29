import logging
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.users.crud import get_user_by_id, get_user_by_name
from src.api_v1.users.schemas import AuthResponse, LoginRequest, UserInfo
from src.core.config import REFRESH_COOKIE_NAME, setting
from src.core.database import get_async_session, get_redis_connection
from src.core.jwt_utils import create_jwt, decode_jwt, validate_password

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


def _refresh_key(user_id: str, jti: str) -> str:
    return f"auth:refresh:{user_id}:{jti}"


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверное имя пользователя или пароль",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _redis_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Сервис сессий временно недоступен",
    )


def _set_refresh_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=setting.cookie_secure,
        samesite="lax",
        path="/api/auth",
    )


def _delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/auth",
        secure=setting.cookie_secure,
        httponly=True,
        samesite="lax",
    )


def _create_token_pair(user_id: UUID, auth_version: int) -> tuple[str, str, str, int]:
    access_token, _, _ = create_jwt(
        user_id=str(user_id),
        auth_version=auth_version,
        token_type="access",
        expire_minutes=setting.auth_jwt.access_token_expire_minutes,
    )
    refresh_token, refresh_jti, refresh_ttl = create_jwt(
        user_id=str(user_id),
        auth_version=auth_version,
        token_type="refresh",
        expire_minutes=setting.auth_jwt.refresh_token_expire_minutes,
    )
    return access_token, refresh_token, refresh_jti, refresh_ttl


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_connection),
) -> AuthResponse:
    user = await get_user_by_name(session, data.username.strip())
    if user is None or not await validate_password(data.password, user.hashed_password):
        raise _unauthorized()
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Учетная запись отключена")

    access_token, refresh_token, refresh_jti, refresh_ttl = _create_token_pair(
        user.id, user.auth_version
    )
    try:
        await redis.set(_refresh_key(str(user.id), refresh_jti), "active", ex=refresh_ttl)
    except RedisError as exc:
        logger.warning("Redis is unavailable during login: %s", exc)
        raise _redis_unavailable() from exc

    _set_refresh_cookie(response, refresh_token, refresh_ttl)
    return AuthResponse(access_token=access_token, user=UserInfo.from_user(user))


@router.post("/refresh", response_model=AuthResponse)
async def refresh_session(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    redis: Redis = Depends(get_redis_connection),
) -> AuthResponse:
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise _unauthorized()

    try:
        payload = decode_jwt(refresh_token, expected_type="refresh")
        user_id = UUID(payload["sub"])
        auth_version = int(payload["auth_version"])
        old_jti = str(payload["jti"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise _unauthorized() from exc

    user = await get_user_by_id(session, user_id)
    if user is None or not user.is_active or user.auth_version != auth_version:
        raise _unauthorized()

    old_key = _refresh_key(str(user.id), old_jti)
    try:
        if not await redis.getdel(old_key):
            raise _unauthorized()
        access_token, new_refresh_token, new_jti, refresh_ttl = _create_token_pair(
            user.id, user.auth_version
        )
        await redis.set(_refresh_key(str(user.id), new_jti), "active", ex=refresh_ttl)
    except HTTPException:
        raise
    except RedisError as exc:
        logger.warning("Redis is unavailable during refresh: %s", exc)
        raise _redis_unavailable() from exc

    _set_refresh_cookie(response, new_refresh_token, refresh_ttl)
    return AuthResponse(access_token=access_token, user=UserInfo.from_user(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    redis: Redis = Depends(get_redis_connection),
) -> Response:
    response: Response = Response(status_code=status.HTTP_204_NO_CONTENT)
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if refresh_token:
        try:
            payload = decode_jwt(refresh_token, expected_type="refresh")
            await redis.delete(_refresh_key(str(payload["sub"]), str(payload["jti"])))
        except jwt.InvalidTokenError:
            pass
        except RedisError as exc:
            logger.warning("Redis is unavailable during logout: %s", exc)
            error_response = JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Сервис сессий временно недоступен"},
            )
            _delete_refresh_cookie(error_response)
            return error_response

    _delete_refresh_cookie(response)
    return response
