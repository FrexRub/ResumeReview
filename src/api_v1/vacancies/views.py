from pathlib import Path
from urllib.parse import quote
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from src.api_v1.vacancies.schemas import (
    ActiveVacancyRead,
    ParsedVacancy,
    VacancyCreate,
    VacancyCreated,
    VacancyResumeRead,
)
from src.api_v1.vacancies.service import (
    ResumeNotFound,
    ResumePathInvalid,
    VacancyReadUnavailable,
    VacancyStorageUnavailable,
    YandexDiskTimeout,
    YandexDiskUnavailable,
    get_current_active_vacancy,
    get_parserdoc_client,
    get_unviewed_resumes_for_active_vacancy,
    get_yandex_disk_client,
    open_resume_download,
    save_vacancy,
    stream_resume_download,
)
from src.core.config import setting
from src.core.database import get_async_session
from src.core.depends import current_user_authorization
from src.models.user import User

router = APIRouter(prefix="/vacancies", tags=["Vacancies"])

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".rtf",
    ".xls",
    ".txt",
    ".csv",
    ".html",
    ".htm",
    ".json",
    ".xml",
}
CHUNK_SIZE = 1024 * 1024


@router.get("/active", response_model=ActiveVacancyRead | None)
async def read_active_vacancy(
    _: User = Depends(current_user_authorization),
    session: AsyncSession = Depends(get_async_session),
) -> ActiveVacancyRead | None:
    try:
        vacancy = await get_current_active_vacancy(session)
    except VacancyReadUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Не удалось получить активную вакансию. Попробуйте ещё раз",
        ) from exc
    if vacancy is None:
        return None
    return ActiveVacancyRead.model_validate(vacancy)


@router.get("/active/resumes", response_model=list[VacancyResumeRead])
async def read_active_vacancy_unviewed_resumes(
    _: User = Depends(current_user_authorization),
    session: AsyncSession = Depends(get_async_session),
) -> list[VacancyResumeRead]:
    try:
        resumes = await get_unviewed_resumes_for_active_vacancy(session)
    except VacancyReadUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Не удалось получить резюме для активной вакансии. Попробуйте ещё раз",
        ) from exc
    return [VacancyResumeRead.model_validate(resume) for resume in resumes]


@router.get("/resumes/{resume_id}/download", response_class=StreamingResponse)
async def download_resume(
    resume_id: UUID,
    _: User = Depends(current_user_authorization),
    session: AsyncSession = Depends(get_async_session),
    client: httpx.AsyncClient = Depends(get_yandex_disk_client),
) -> StreamingResponse:
    try:
        download = await open_resume_download(session, resume_id, client)
    except ResumeNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Резюме или файл на Яндекс Диске не найден",
        ) from exc
    except ResumePathInvalid as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Для резюме не указан корректный путь на Яндекс Диске",
        ) from exc
    except VacancyReadUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Не удалось получить данные резюме",
        ) from exc
    except YandexDiskTimeout as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Яндекс Диск не успел подготовить файл",
        ) from exc
    except YandexDiskUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Не удалось скачать резюме с Яндекс Диска",
        ) from exc

    suffix = Path(download.filename).suffix.lower()
    safe_suffix = suffix if len(suffix) <= 10 and suffix[1:].isalnum() else ""
    fallback_filename = f"resume{safe_suffix}"
    disposition = (
        f'attachment; filename="{fallback_filename}"; '
        f"filename*=UTF-8''{quote(download.filename)}"
    )
    headers = {"Content-Disposition": disposition}
    content_length = download.response.headers.get("content-length")
    if content_length and content_length.isdigit():
        headers["Content-Length"] = content_length
    return StreamingResponse(
        stream_resume_download(download.response),
        media_type=download.response.headers.get(
            "content-type", "application/octet-stream"
        ),
        headers=headers,
    )


@router.post("", response_model=VacancyCreated, status_code=status.HTTP_201_CREATED)
async def create_vacancy(
    data: VacancyCreate,
    _: User = Depends(current_user_authorization),
    session: AsyncSession = Depends(get_async_session),
) -> VacancyCreated:
    try:
        vacancy = await save_vacancy(session, data.content, data.filename)
    except VacancyStorageUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Не удалось сохранить вакансию. Попробуйте ещё раз",
        ) from exc
    return VacancyCreated.model_validate(vacancy)


async def _read_limited(file: UploadFile) -> bytes:
    content = bytearray()
    while chunk := await file.read(CHUNK_SIZE):
        content.extend(chunk)
        if len(content) > setting.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="Файл превышает допустимый размер 20 МБ",
            )
    return bytes(content)


def _parser_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return "ParserDoc вернул некорректный ответ"
    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("error")
        if isinstance(detail, str):
            return detail
    return "Не удалось обработать документ"


@router.post("/parse", response_model=ParsedVacancy)
async def parse_vacancy(
    file: UploadFile = File(...),
    _: User = Depends(current_user_authorization),
    client: httpx.AsyncClient = Depends(get_parserdoc_client),
) -> ParsedVacancy:
    filename = file.filename or "document"
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Неподдерживаемый формат файла",
        )

    try:
        content = await _read_limited(file)
    finally:
        await file.close()

    try:
        parser_response = await client.post(
            "/parse",
            files={
                "file": (
                    filename,
                    content,
                    file.content_type or "application/octet-stream",
                )
            },
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="ParserDoc не успел обработать файл",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ParserDoc временно недоступен",
        ) from exc

    if parser_response.status_code == status.HTTP_413_CONTENT_TOO_LARGE:
        raise HTTPException(
            status_code=413, detail=_parser_error_detail(parser_response)
        )
    if parser_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        raise HTTPException(
            status_code=422, detail=_parser_error_detail(parser_response)
        )
    if parser_response.is_error:
        raise HTTPException(
            status_code=502, detail=_parser_error_detail(parser_response)
        )

    try:
        return ParsedVacancy.model_validate(parser_response.json())
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ParserDoc вернул некорректный ответ",
        ) from exc
