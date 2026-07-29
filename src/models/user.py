from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class User(Base):
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=datetime.utcnow,
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    auth_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, username={self.name!r})"

    def __repr__(self) -> str:
        return str(self)
