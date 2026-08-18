from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.api_v1.vacancies import service
from src.api_v1.vacancies.crud import (
    get_active_vacancy_filename,
    get_unviewed_resumes_by_vacancy_title,
)
from src.api_v1.vacancies.service import VacancyReadUnavailable


class ActiveVacancyResult:
    def __init__(self, filename: str | None) -> None:
        self.filename = filename

    def scalar_one_or_none(self) -> str | None:
        return self.filename


class ResumeScalars:
    def __init__(self, resumes: list[object]) -> None:
        self.resumes = resumes

    def all(self) -> list[object]:
        return self.resumes


class ResumeResult:
    def __init__(self, resumes: list[object]) -> None:
        self.resumes = resumes

    def scalars(self) -> ResumeScalars:
        return ResumeScalars(self.resumes)


@pytest.mark.asyncio
async def test_active_vacancy_query_filters_active_and_prefers_latest() -> None:
    session = AsyncMock()
    session.execute.return_value = ActiveVacancyResult("vacancy.txt")

    filename = await get_active_vacancy_filename(session)

    statement = str(session.execute.await_args.args[0])
    assert filename == "vacancy.txt"
    assert "vacancys.is_active IS true" in statement
    assert "vacancys.created_at DESC" in statement
    assert "LIMIT" in statement


@pytest.mark.asyncio
async def test_resume_query_filters_title_and_unviewed() -> None:
    expected = [object()]
    session = AsyncMock()
    session.execute.return_value = ResumeResult(expected)

    resumes = await get_unviewed_resumes_by_vacancy_title(session, "vacancy.txt")

    statement = str(session.execute.await_args.args[0])
    assert resumes == expected
    assert "vacancy_resume.title_vacancy =" in statement
    assert "vacancy_resume.viewed IS false" in statement


@pytest.mark.asyncio
async def test_service_returns_empty_when_there_is_no_active_vacancy(
    monkeypatch,
) -> None:
    find_filename = AsyncMock(return_value=None)
    find_resumes = AsyncMock()
    monkeypatch.setattr(service, "get_active_vacancy_filename", find_filename)
    monkeypatch.setattr(
        service,
        "get_unviewed_resumes_by_vacancy_title",
        find_resumes,
    )

    assert await service.get_unviewed_resumes_for_active_vacancy(AsyncMock()) == []
    find_resumes.assert_not_awaited()


@pytest.mark.asyncio
async def test_service_maps_database_error(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "get_active_vacancy_filename",
        AsyncMock(side_effect=SQLAlchemyError("unavailable")),
    )

    with pytest.raises(VacancyReadUnavailable):
        await service.get_unviewed_resumes_for_active_vacancy(AsyncMock())
