from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.vacancy import Vacancy
from src.models.vacancy_resume import VacancyResume


async def create_vacancy(
    session: AsyncSession,
    content: str,
    filename: str,
) -> Vacancy:
    vacancy = Vacancy(content=content, filename=filename, is_active=True)
    session.add(vacancy)
    await session.flush()
    return vacancy


async def get_active_vacancy(session: AsyncSession) -> Vacancy | None:
    result = await session.execute(
        select(Vacancy)
        .where(Vacancy.is_active.is_(True))
        .order_by(Vacancy.created_at.desc(), Vacancy.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def deactivate_active_vacancy(session: AsyncSession) -> Vacancy | None:
    vacancy = await get_active_vacancy(session)
    if vacancy is None:
        return None
    vacancy.is_active = False
    await session.flush()
    return vacancy


async def get_active_vacancy_filename(session: AsyncSession) -> str | None:
    result = await session.execute(
        select(Vacancy.filename)
        .where(Vacancy.is_active.is_(True))
        .order_by(Vacancy.created_at.desc(), Vacancy.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_unviewed_resumes_by_vacancy_title(
    session: AsyncSession,
    title_vacancy: str,
) -> list[VacancyResume]:
    result = await session.execute(
        select(VacancyResume).where(
            VacancyResume.title_vacancy == title_vacancy,
            VacancyResume.viewed.is_(False),
        )
    )
    return list(result.scalars().all())


async def get_vacancy_resume_by_id(
    session: AsyncSession,
    resume_id: UUID,
) -> VacancyResume | None:
    return await session.get(VacancyResume, resume_id)


async def mark_vacancy_resume_viewed(
    session: AsyncSession,
    resume_id: UUID,
) -> VacancyResume | None:
    resume = await get_vacancy_resume_by_id(session, resume_id)
    if resume is None:
        return None
    resume.viewed = True
    await session.flush()
    return resume
