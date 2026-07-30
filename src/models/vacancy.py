from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, Text, func, true
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Vacancy(Base):
    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, is_active={self.is_active!r})"
