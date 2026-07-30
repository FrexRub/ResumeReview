from collections.abc import AsyncGenerator

import httpx
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.vacancies.crud import create_vacancy
from src.core.config import setting
from src.models.vacancy import Vacancy


class VacancyStorageUnavailable(Exception):
    """Raised when a vacancy cannot be persisted."""


async def get_parserdoc_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        base_url=setting.parserdoc_url.rstrip("/"),
        timeout=httpx.Timeout(setting.parserdoc_timeout_seconds),
    ) as client:
        yield client


async def save_vacancy(
    session: AsyncSession,
    content: str,
    filename: str,
) -> Vacancy:
    try:
        vacancy = await create_vacancy(session, content, filename)
        await session.commit()
        await session.refresh(vacancy)
        return vacancy
    except SQLAlchemyError as exc:
        await session.rollback()
        raise VacancyStorageUnavailable from exc
