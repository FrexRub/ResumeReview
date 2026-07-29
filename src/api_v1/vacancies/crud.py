from sqlalchemy.ext.asyncio import AsyncSession

from src.models.vacancy import Vacancy


async def create_vacancy(session: AsyncSession, content: str) -> Vacancy:
    vacancy = Vacancy(content=content, is_active=True)
    session.add(vacancy)
    await session.flush()
    return vacancy
