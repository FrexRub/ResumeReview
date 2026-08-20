from collections.abc import AsyncGenerator
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import urlparse
from uuid import UUID

import httpx
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api_v1.vacancies.crud import (
    create_vacancy,
    get_active_vacancy_filename,
    get_unviewed_resumes_by_vacancy_title,
    get_vacancy_resume_by_id,
)
from src.core.config import setting
from src.models.vacancy import Vacancy
from src.models.vacancy_resume import VacancyResume


class VacancyStorageUnavailable(Exception):
    """Raised when a vacancy cannot be persisted."""


class VacancyReadUnavailable(Exception):
    """Raised when vacancy resumes cannot be read."""


class ResumeNotFound(Exception):
    """Raised when the requested resume record or file does not exist."""


class ResumePathInvalid(Exception):
    """Raised when a resume does not contain a valid Yandex Disk path."""


class YandexDiskUnavailable(Exception):
    """Raised when Yandex Disk cannot serve the resume."""


class YandexDiskTimeout(Exception):
    """Raised when Yandex Disk does not respond in time."""


@dataclass(slots=True)
class ResumeDownload:
    response: httpx.Response
    filename: str


async def get_parserdoc_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        base_url=setting.parserdoc_url.rstrip("/"),
        timeout=httpx.Timeout(setting.parserdoc_timeout_seconds),
        trust_env=False,
    ) as client:
        yield client


async def get_yandex_disk_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        base_url=setting.yandex_disk_api_url.rstrip("/"),
        timeout=httpx.Timeout(setting.yandex_disk_timeout_seconds),
        trust_env=False,
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


async def get_unviewed_resumes_for_active_vacancy(
    session: AsyncSession,
) -> list[VacancyResume]:
    try:
        filename = await get_active_vacancy_filename(session)
        if filename is None:
            return []
        return await get_unviewed_resumes_by_vacancy_title(session, filename)
    except SQLAlchemyError as exc:
        raise VacancyReadUnavailable from exc


def _is_yandex_download_url(href: str) -> bool:
    parsed = urlparse(href)
    hostname = (parsed.hostname or "").lower()
    is_yandex_host = hostname.endswith(".yandex.ru") or hostname.endswith(".yandex.net")
    return (
        parsed.scheme == "https"
        and parsed.username is None
        and parsed.password is None
        and is_yandex_host
    )


async def open_resume_download(
    session: AsyncSession,
    resume_id: UUID,
    client: httpx.AsyncClient,
) -> ResumeDownload:
    try:
        resume = await get_vacancy_resume_by_id(session, resume_id)
    except SQLAlchemyError as exc:
        raise VacancyReadUnavailable from exc

    if resume is None:
        raise ResumeNotFound

    disk_path = (resume.url_resume or "").strip()
    if not disk_path.startswith("disk:/"):
        raise ResumePathInvalid

    token = setting.yandex_disk_oauth_token.get_secret_value().strip()
    if not token:
        raise YandexDiskUnavailable

    try:
        link_response = await client.get(
            "/v1/disk/resources/download",
            params={"path": disk_path},
            headers={
                "Accept": "application/json",
                "Authorization": f"OAuth {token}",
            },
        )
    except httpx.TimeoutException as exc:
        raise YandexDiskTimeout from exc
    except httpx.RequestError as exc:
        raise YandexDiskUnavailable from exc

    if link_response.status_code == 404:
        raise ResumeNotFound
    if link_response.is_error:
        raise YandexDiskUnavailable

    try:
        payload = link_response.json()
        href = payload["href"]
    except (ValueError, KeyError, TypeError) as exc:
        raise YandexDiskUnavailable from exc
    if not isinstance(href, str) or not _is_yandex_download_url(href):
        raise YandexDiskUnavailable

    try:
        download_response = await client.send(
            client.build_request("GET", href),
            stream=True,
            follow_redirects=True,
        )
    except httpx.TimeoutException as exc:
        raise YandexDiskTimeout from exc
    except httpx.RequestError as exc:
        raise YandexDiskUnavailable from exc

    if download_response.status_code == 404:
        await download_response.aclose()
        raise ResumeNotFound
    if download_response.is_error:
        await download_response.aclose()
        raise YandexDiskUnavailable

    filename = PurePosixPath(disk_path.removeprefix("disk:")).name
    if not filename:
        await download_response.aclose()
        raise ResumePathInvalid
    return ResumeDownload(response=download_response, filename=filename)


async def stream_resume_download(
    response: httpx.Response,
) -> AsyncIterator[bytes]:
    try:
        async for chunk in response.aiter_bytes():
            yield chunk
    finally:
        await response.aclose()
