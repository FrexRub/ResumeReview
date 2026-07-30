from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParsedVacancy(BaseModel):
    status: str = "ok"
    filename: str | None = None
    mime_type: str | None = None
    source_type: str
    characters: int = Field(ge=0)
    text: str
    warnings: list[str] = Field(default_factory=list)


class VacancyCreate(BaseModel):
    content: str = Field(min_length=1)
    filename: str = Field(min_length=1)

    @field_validator("content", "filename")
    @classmethod
    def fields_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Поле не должно быть пустым")
        return value


class VacancyCreated(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    is_active: bool
