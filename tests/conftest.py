from collections.abc import Generator
from datetime import datetime, timezone
from uuid import uuid4

import bcrypt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from src.core.config import setting
from src.core.database import get_async_session, get_redis_connection
from src.main import app
from src.models.user import User


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self.values[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def getdel(self, key: str) -> str | None:
        return self.values.pop(key, None)

    async def delete(self, key: str) -> int:
        return int(self.values.pop(key, None) is not None)


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.committed = False
        self.rolled_back = False

    def add(self, entity: object) -> None:
        self.added.append(entity)

    async def flush(self) -> None:
        entity = self.added[-1]
        if getattr(entity, "id", None) is None:
            setattr(entity, "id", len(self.added))

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, entity: object) -> None:
        if getattr(entity, "created_at", None) is None:
            setattr(entity, "created_at", datetime.now(timezone.utc))

    async def rollback(self) -> None:
        self.rolled_back = True


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setattr(setting, "secret_key", SecretStr("test-secret-for-resume-review-2026"))


@pytest.fixture
def user() -> User:
    hashed_password = bcrypt.hashpw(b"Strong!Pass1", bcrypt.gensalt()).decode("utf-8")
    return User(
        id=uuid4(),
        name="revisor",
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        auth_version=0,
        registered_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def client(redis: FakeRedis, session: FakeSession) -> Generator[TestClient, None, None]:
    async def session_override():
        yield session

    async def redis_override():
        yield redis

    app.dependency_overrides[get_async_session] = session_override
    app.dependency_overrides[get_redis_connection] = redis_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
