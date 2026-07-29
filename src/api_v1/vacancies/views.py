from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError

from src.api_v1.vacancies.schemas import ParsedVacancy
from src.api_v1.vacancies.service import get_parserdoc_client
from src.core.config import setting
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
            files={"file": (filename, content, file.content_type or "application/octet-stream")},
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
        raise HTTPException(status_code=413, detail=_parser_error_detail(parser_response))
    if parser_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        raise HTTPException(status_code=422, detail=_parser_error_detail(parser_response))
    if parser_response.is_error:
        raise HTTPException(status_code=502, detail=_parser_error_detail(parser_response))

    try:
        return ParsedVacancy.model_validate(parser_response.json())
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ParserDoc вернул некорректный ответ",
        ) from exc
