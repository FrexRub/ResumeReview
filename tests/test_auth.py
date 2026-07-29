from uuid import UUID

import jwt
import pytest
from fastapi import HTTPException

from src.api_v1.auth import views as auth_views
from src.api_v1.users import views as user_views
from src.core import depends
from src.core.config import REFRESH_COOKIE_NAME, setting
from src.core.jwt_utils import create_jwt, decode_jwt, validate_password


@pytest.mark.asyncio
async def test_login_refresh_and_logout(client, user, redis, monkeypatch):
    async def find_by_name(_session, username):
        return user if username == user.name else None

    async def find_by_id(_session, user_id):
        return user if user_id == user.id else None

    monkeypatch.setattr(auth_views, "get_user_by_name", find_by_name)
    monkeypatch.setattr(auth_views, "get_user_by_id", find_by_id)

    response = client.post(
        "/api/auth/login",
        json={"username": "revisor", "password": "Strong!Pass1"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "revisor"
    assert response.json()["token_type"] == "bearer"
    assert REFRESH_COOKIE_NAME in response.cookies
    old_keys = set(redis.values)
    assert len(old_keys) == 1

    refreshed = client.post("/api/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"] != response.json()["access_token"]
    assert old_keys.isdisjoint(redis.values)

    logged_out = client.post("/api/auth/logout")
    assert logged_out.status_code == 204
    assert not redis.values


@pytest.mark.asyncio
async def test_login_rejects_bad_password_and_inactive_user(client, user, monkeypatch):
    async def find_user(_session, _username):
        return user

    monkeypatch.setattr(auth_views, "get_user_by_name", find_user)
    bad_password = client.post(
        "/api/auth/login",
        json={"username": "revisor", "password": "Wrong!Pass1"},
    )
    assert bad_password.status_code == 401

    user.is_active = False
    inactive = client.post(
        "/api/auth/login",
        json={"username": "revisor", "password": "Strong!Pass1"},
    )
    assert inactive.status_code == 403


@pytest.mark.asyncio
async def test_expired_and_wrong_type_tokens_are_rejected(user, session, monkeypatch):
    async def find_by_id(_session, user_id: UUID):
        return user if user_id == user.id else None

    monkeypatch.setattr(depends, "get_user_by_id", find_by_id)
    expired, _, _ = create_jwt(
        user_id=str(user.id), auth_version=0, token_type="access", expire_minutes=-1
    )
    with pytest.raises(HTTPException) as expired_error:
        await depends.current_user_authorization(expired, session)
    assert expired_error.value.status_code == 401

    refresh, _, _ = create_jwt(
        user_id=str(user.id), auth_version=0, token_type="refresh", expire_minutes=5
    )
    with pytest.raises(HTTPException) as type_error:
        await depends.current_user_authorization(refresh, session)
    assert type_error.value.status_code == 401


@pytest.mark.asyncio
async def test_change_password_revokes_old_token(client, user, session, monkeypatch):
    async def update_password(_session, target_user, hashed_password):
        target_user.hashed_password = hashed_password
        target_user.auth_version += 1
        return target_user

    async def find_by_id(_session, _user_id):
        return user

    from src.core.depends import current_user_authorization
    from src.main import app

    app.dependency_overrides[current_user_authorization] = lambda: user
    monkeypatch.setattr(user_views, "update_user_password", update_password)

    old_token, _, _ = create_jwt(
        user_id=str(user.id), auth_version=0, token_type="access", expire_minutes=5
    )
    response = client.post(
        "/api/users/me/change-password",
        json={"current_password": "Strong!Pass1", "new_password": "New!Strong2"},
        headers={"Authorization": f"Bearer {old_token}"},
    )
    assert response.status_code == 204
    assert user.auth_version == 1
    assert await validate_password("New!Strong2", user.hashed_password)

    app.dependency_overrides.pop(current_user_authorization, None)
    monkeypatch.setattr(depends, "get_user_by_id", find_by_id)
    with pytest.raises(HTTPException):
        await depends.current_user_authorization(old_token, session)


@pytest.mark.asyncio
async def test_password_policy(client, user):
    from src.core.depends import current_user_authorization
    from src.main import app

    app.dependency_overrides[current_user_authorization] = lambda: user
    response = client.post(
        "/api/users/me/change-password",
        json={"current_password": "Strong!Pass1", "new_password": "weakpass"},
    )
    assert response.status_code == 422



def test_login_returns_503_when_redis_is_unavailable(client, user, redis, monkeypatch):
    from redis.exceptions import RedisError

    async def find_user(_session, _username):
        return user

    async def broken_set(*_args, **_kwargs):
        raise RedisError("unavailable")

    monkeypatch.setattr(auth_views, "get_user_by_name", find_user)
    monkeypatch.setattr(redis, "set", broken_set)
    response = client.post(
        "/api/auth/login",
        json={"username": "revisor", "password": "Strong!Pass1"},
    )
    assert response.status_code == 503
