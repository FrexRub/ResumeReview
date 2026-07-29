from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.users.crud import update_user_password
from src.api_v1.users.schemas import ChangePasswordRequest, UserInfo
from src.core.config import REFRESH_COOKIE_NAME, setting
from src.core.database import get_async_session
from src.core.depends import current_user_authorization
from src.core.jwt_utils import create_hash_password, validate_password
from src.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserInfo)
async def get_current_user(user: User = Depends(current_user_authorization)) -> UserInfo:
    return UserInfo.from_user(user)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(current_user_authorization),
    session: AsyncSession = Depends(get_async_session),
) -> Response:
    if not await validate_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Текущий пароль неверен")
    if await validate_password(data.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новый пароль должен отличаться от текущего",
        )

    hashed_password = await create_hash_password(data.new_password)
    await update_user_password(session, user, hashed_password)

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/auth",
        secure=setting.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return response
