from pydantic import BaseModel, Field


class ParsedVacancy(BaseModel):
    status: str = "ok"
    filename: str | None = None
    mime_type: str | None = None
    source_type: str
    characters: int = Field(ge=0)
    text: str
    warnings: list[str] = Field(default_factory=list)
