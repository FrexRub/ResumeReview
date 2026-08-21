from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.api_v1.vacancies import service
from src.api_v1.vacancies.crud import (
    deactivate_active_vacancy,
    get_active_vacancy,
    get_active_vacancy_filename,
    get_unviewed_resumes_by_vacancy_title,
    mark_vacancy_resume_viewed,
)
from src.api_v1.vacancies.service import VacancyReadUnavailable
from src.models.vacancy import Vacancy
from src.models.vacancy_resume import VacancyResume


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
async def test_active_vacancy_query_returns_latest_active_record() -> None:
    vacancy = Vacancy(
        id=7,
        content="Backend Developer",
        filename="backend-developer.txt",
        is_active=True,
    )
    session = AsyncMock()
    session.execute.return_value = ActiveVacancyResult(vacancy)

    result = await get_active_vacancy(session)

    statement = str(session.execute.await_args.args[0])
    assert result is vacancy
    assert "vacancys.is_active IS true" in statement
    assert "vacancys.created_at DESC" in statement
    assert "LIMIT" in statement


@pytest.mark.asyncio
async def test_deactivate_active_vacancy_updates_current_record() -> None:
    vacancy = Vacancy(
        id=7,
        content="Backend Developer",
        filename="backend-developer.txt",
        is_active=True,
    )
    session = AsyncMock()
    session.execute.return_value = ActiveVacancyResult(vacancy)

    result = await deactivate_active_vacancy(session)

    assert result is vacancy
    assert vacancy.is_active is False
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_deactivate_current_vacancy_commits_change(monkeypatch) -> None:
    vacancy = Vacancy(
        id=7,
        content="Backend Developer",
        filename="backend-developer.txt",
        is_active=False,
    )
    deactivate = AsyncMock(return_value=vacancy)
    monkeypatch.setattr(service, "deactivate_active_vacancy", deactivate)
    session = AsyncMock()

    result = await service.deactivate_current_vacancy(session)

    assert result is vacancy
    deactivate.assert_awaited_once_with(session)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(vacancy)


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
async def test_mark_vacancy_resume_viewed_updates_record() -> None:
    resume = VacancyResume(id=uuid4(), viewed=False)
    session = AsyncMock()
    session.get.return_value = resume

    result = await mark_vacancy_resume_viewed(session, resume.id)

    assert result is resume
    assert resume.viewed is True
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_resume_as_viewed_commits_change(monkeypatch) -> None:
    resume = VacancyResume(id=uuid4(), viewed=True)
    update = AsyncMock(return_value=resume)
    monkeypatch.setattr(service, "mark_vacancy_resume_viewed", update)
    session = AsyncMock()

    result = await service.mark_resume_as_viewed(session, resume.id)

    assert result is resume
    update.assert_awaited_once_with(session, resume.id)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(resume)


@pytest.mark.asyncio
async def test_mark_resume_as_viewed_rolls_back_database_error(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "mark_vacancy_resume_viewed",
        AsyncMock(side_effect=SQLAlchemyError("unavailable")),
    )
    session = AsyncMock()

    with pytest.raises(service.ResumeStorageUnavailable):
        await service.mark_resume_as_viewed(session, uuid4())

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


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
async def test_current_active_vacancy_service_maps_database_error(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "get_active_vacancy",
        AsyncMock(side_effect=SQLAlchemyError("unavailable")),
    )

    with pytest.raises(VacancyReadUnavailable):
        await service.get_current_active_vacancy(AsyncMock())


@pytest.mark.asyncio
async def test_service_maps_database_error(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "get_active_vacancy_filename",
        AsyncMock(side_effect=SQLAlchemyError("unavailable")),
    )

    with pytest.raises(VacancyReadUnavailable):
        await service.get_unviewed_resumes_for_active_vacancy(AsyncMock())
