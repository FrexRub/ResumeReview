import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

import bcrypt
import jwt

from src.core.config import setting

TokenType = Literal["access", "refresh"]


async def create_hash_password(password: str) -> str:
    return await asyncio.to_thread(
        lambda: bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    )


async def validate_password(password: str, hashed_password: str) -> bool:
    try:
        return await asyncio.to_thread(
            bcrypt.checkpw,
            password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_jwt(
    *,
    user_id: str,
    auth_version: int,
    token_type: TokenType,
    expire_minutes: int,
) -> tuple[str, str, int]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expire_minutes)
    jti = str(uuid4())
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": token_type,
        "jti": jti,
        "auth_version": auth_version,
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(
        payload,
        setting.secret_key.get_secret_value(),
        algorithm=setting.auth_jwt.algorithm,
    )
    return token, jti, int((expires_at - now).total_seconds())


def decode_jwt(token: str, *, expected_type: TokenType) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        setting.secret_key.get_secret_value(),
        algorithms=[setting.auth_jwt.algorithm],
        options={"require": ["sub", "type", "jti", "auth_version", "iat", "exp"]},
    )
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload
