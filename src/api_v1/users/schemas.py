import re
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
)

PATTERN_PASSWORD = (
    r'^(?=.*?[a-z])(?=.*?[A-Z])(?=.*?[0-9])(?=.*?[!"#\$%&\(\)\*\+,-\.\/:;<=>\?@[\]\^_'
    r"`\{\|}~])[a-zA-Z0-9!\$%&\(\)\*\+,-\.\/:;<=>\?@[\]\^_`\{\|}~]{8,}$"
)


class UserBaseSchemas(BaseModel):
    full_name: Optional[str]
    email: EmailStr


class UserUpdateSchemas(UserBaseSchemas):
    pass


class UserUpdatePartialSchemas(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserCreateSchemas(BaseModel):
    full_name: str = Field(alias="username")
    email: EmailStr
    hashed_password: str = Field(alias="password")

    @field_validator("hashed_password")
    def validate_password(cls, value: str) -> str:
        if not re.match(PATTERN_PASSWORD, value):
            raise ValueError("Пароль должен состоять из цифр, букв (с заглавной) и специальных символов")
        return value


class UserInfoSchemas(UserBaseSchemas):
    id: str
    is_active: bool
    is_verified: bool


class OutUserSchemas(BaseModel):
    access_token: str
    token_type: str
    user: UserInfoSchemas


class LoginSchemas(BaseModel):
    username: str
    password: str


class TokenSchemas(BaseModel):
    access_token: str
