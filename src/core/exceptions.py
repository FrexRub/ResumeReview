from typing import Optional

from fastapi import HTTPException, status


class ExceptAuthentication(HTTPException):
    def __init__(self, detail: Optional[str] = None) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail or "Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )


class NotFindUser(Exception):
    pass


class NotFindData(Exception):
    pass


class ExceptDB(Exception):
    pass


class ExceptUser(Exception):
    pass


class ErrorInData(Exception):
    pass


class EmailInUse(Exception):
    pass


class UniqueViolationError(Exception):
    pass
