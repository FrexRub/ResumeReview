from sqlalchemy.ext.asyncio import AsyncSession

from src.models.vacancy import Vacancy


async def create_vacancy(
    session: AsyncSession,
    content: str,
    filename: str,
) -> Vacancy:
    vacancy = Vacancy(content=content, filename=filename, is_active=True)
    session.add(vacancy)
    await session.flush()
    return vacancy
