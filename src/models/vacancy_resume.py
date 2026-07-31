from sqlalchemy import BigInteger, Boolean, Identity, Text, false
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class VacancyResume(Base):
    title_vacancy: Mapped[str | None] = mapped_column(Text)
    desired_position: Mapped[str | None] = mapped_column(Text)
    summary_resume: Mapped[str | None] = mapped_column(Text)
    score_label: Mapped[str | None] = mapped_column(Text)
    candidate_rating: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    recommendation_reason: Mapped[str | None] = mapped_column(Text)
    executive_summary: Mapped[str | None] = mapped_column(Text)
    short_conclusion: Mapped[str | None] = mapped_column(Text)
    url_resume: Mapped[str | None] = mapped_column(Text)
    viewed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id}, "
            f"title_vacancy={self.title_vacancy!r})"
        )
