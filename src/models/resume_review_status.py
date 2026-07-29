from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Index, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class ResumeReviewStatus(Base):
    """Processing status of an email handled by the n8n ResumeReview workflow."""

    __tablename__ = "my_ResumeReviewStatus"
    __table_args__ = (
        Index(
            "ResumeReviewStatus_channel_ID_message_key",
            "channel",
            "id_message",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    id_message: Mapped[str] = mapped_column(Text, nullable=False)
    date_message: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    sender: Mapped[str | None] = mapped_column(Text)
    topic_messag: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="new",
        server_default=text("'new'::text"),
    )
    type_messag: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id}, "
            f"channel={self.channel!r}, id_message={self.id_message!r}, "
            f"status={self.status!r})"
        )
