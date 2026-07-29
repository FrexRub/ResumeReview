import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!\"#$%&'()*+,\-./:;<=>?@[\]^_`{|}~]).{8,128}$"
)
PASSWORD_MESSAGE = (
    "Пароль должен содержать минимум 8 символов, строчную и заглавную буквы, "
    "цифру и специальный символ"
)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)


class UserInfo(BaseModel):
    id: UUID
    username: str
    is_active: bool
    is_superuser: bool
    registered_at: datetime

    @classmethod
    def from_user(cls, user: object) -> "UserInfo":
        return cls(
            id=getattr(user, "id"),
            username=getattr(user, "name"),
            is_active=getattr(user, "is_active"),
            is_superuser=getattr(user, "is_superuser"),
            registered_at=getattr(user, "registered_at"),
        )


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if not PASSWORD_PATTERN.match(value):
            raise ValueError(PASSWORD_MESSAGE)
        return value
