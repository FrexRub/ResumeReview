from uuid import uuid4

import httpx
import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.api_v1.vacancies import views as vacancy_views
from src.api_v1.vacancies.service import (
    VacancyReadUnavailable,
    get_parserdoc_client,
)
from src.core.config import setting
from src.core.depends import current_user_authorization
from src.main import app
from src.models.vacancy_resume import VacancyResume

PARSED = {
    "status": "ok",
    "filename": "vacancy.txt",
    "mime_type": "text/plain",
    "source_type": "text",
    "characters": 17,
    "text": "Python developer",
    "warnings": [],
}


def parser_client(handler):
    return httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://parserdoc.example",
    )


def test_parse_vacancy_success(client, user):
    async def client_override():
        async with parser_client(
            lambda request: httpx.Response(200, json=PARSED)
        ) as parser:
            yield parser

    app.dependency_overrides[current_user_authorization] = lambda: user
    app.dependency_overrides[get_parserdoc_client] = client_override
    response = client.post(
        "/api/vacancies/parse",
        files={"file": ("vacancy.txt", b"Python developer", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["text"] == "Python developer"


def test_parse_requires_authorization(client):
    response = client.post(
        "/api/vacancies/parse",
        files={"file": ("vacancy.txt", b"content", "text/plain")},
    )
    assert response.status_code == 401


def test_save_vacancy_success(client, user, session):
    app.dependency_overrides[current_user_authorization] = lambda: user

    response = client.post(
        "/api/vacancies",
        json={"content": "Python developer", "filename": "vacancy.txt"},
    )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["is_active"] is True
    assert session.committed is True
    assert len(session.added) == 1
    assert session.added[0].content == "Python developer"
    assert session.added[0].filename == "vacancy.txt"


def test_save_vacancy_requires_authorization(client):
    response = client.post(
        "/api/vacancies",
        json={"content": "Python developer", "filename": "vacancy.txt"},
    )

    assert response.status_code == 401


def test_get_unviewed_resumes_for_active_vacancy(client, user, monkeypatch):
    resume_id = uuid4()
    resume = VacancyResume(
        id=resume_id,
        title_vacancy="vacancy.txt",
        desired_position="Python developer",
        summary_resume="Five years of experience",
        score_label="high",
        candidate_rating=91,
        recommendation="invite",
        recommendation_reason="Relevant experience",
        executive_summary="Strong candidate",
        short_conclusion="Invite",
        url_resume="https://example.test/resume/1",
        viewed=False,
    )

    async def find_resumes(_session):
        return [resume]

    monkeypatch.setattr(
        vacancy_views,
        "get_unviewed_resumes_for_active_vacancy",
        find_resumes,
    )
    app.dependency_overrides[current_user_authorization] = lambda: user

    response = client.get("/api/vacancies/active/resumes")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(resume_id),
            "title_vacancy": "vacancy.txt",
            "desired_position": "Python developer",
            "summary_resume": "Five years of experience",
            "score_label": "high",
            "candidate_rating": 91,
            "recommendation": "invite",
            "recommendation_reason": "Relevant experience",
            "executive_summary": "Strong candidate",
            "short_conclusion": "Invite",
            "url_resume": "https://example.test/resume/1",
            "viewed": False,
        }
    ]


def test_get_unviewed_resumes_returns_empty_list(client, user, monkeypatch):
    async def find_resumes(_session):
        return []

    monkeypatch.setattr(
        vacancy_views,
        "get_unviewed_resumes_for_active_vacancy",
        find_resumes,
    )
    app.dependency_overrides[current_user_authorization] = lambda: user

    response = client.get("/api/vacancies/active/resumes")

    assert response.status_code == 200
    assert response.json() == []


def test_get_unviewed_resumes_requires_authorization(client):
    response = client.get("/api/vacancies/active/resumes")

    assert response.status_code == 401


def test_get_unviewed_resumes_maps_database_failure(client, user, monkeypatch):
    async def fail_read(_session):
        raise VacancyReadUnavailable

    monkeypatch.setattr(
        vacancy_views,
        "get_unviewed_resumes_for_active_vacancy",
        fail_read,
    )
    app.dependency_overrides[current_user_authorization] = lambda: user

    response = client.get("/api/vacancies/active/resumes")

    assert response.status_code == 503


def test_save_vacancy_rejects_blank_content(client, user):
    app.dependency_overrides[current_user_authorization] = lambda: user

    response = client.post(
        "/api/vacancies",
        json={"content": "   ", "filename": "vacancy.txt"},
    )

    assert response.status_code == 422


def test_save_vacancy_rejects_blank_filename(client, user):
    app.dependency_overrides[current_user_authorization] = lambda: user

    response = client.post(
        "/api/vacancies",
        json={"content": "Python developer", "filename": "   "},
    )

    assert response.status_code == 422


def test_save_vacancy_maps_database_failure(client, user, session, monkeypatch):
    async def fail_flush() -> None:
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(session, "flush", fail_flush)
    app.dependency_overrides[current_user_authorization] = lambda: user

    response = client.post(
        "/api/vacancies",
        json={"content": "Python developer", "filename": "vacancy.txt"},
    )

    assert response.status_code == 503
    assert session.rolled_back is True


def test_rejects_format_and_oversized_file(client, user, monkeypatch):
    app.dependency_overrides[current_user_authorization] = lambda: user
    unsupported = client.post(
        "/api/vacancies/parse",
        files={"file": ("vacancy.exe", b"content", "application/octet-stream")},
    )
    assert unsupported.status_code == 422

    monkeypatch.setattr(setting, "max_upload_bytes", 5)
    oversized = client.post(
        "/api/vacancies/parse",
        files={"file": ("vacancy.txt", b"too large", "text/plain")},
    )
    assert oversized.status_code == 413


@pytest.mark.parametrize(
    ("parser_status", "expected_status"),
    [(422, 422), (500, 502)],
)
def test_maps_parser_errors(client, user, parser_status, expected_status):
    async def client_override():
        async with parser_client(
            lambda request: httpx.Response(
                parser_status, json={"detail": "parse failed"}
            )
        ) as parser:
            yield parser

    app.dependency_overrides[current_user_authorization] = lambda: user
    app.dependency_overrides[get_parserdoc_client] = client_override
    response = client.post(
        "/api/vacancies/parse",
        files={"file": ("vacancy.txt", b"content", "text/plain")},
    )
    assert response.status_code == expected_status


def test_maps_parser_timeout(client, user):
    def timeout_handler(request):
        raise httpx.ReadTimeout("timeout", request=request)

    async def client_override():
        async with parser_client(timeout_handler) as parser:
            yield parser

    app.dependency_overrides[current_user_authorization] = lambda: user
    app.dependency_overrides[get_parserdoc_client] = client_override
    response = client.post(
        "/api/vacancies/parse",
        files={"file": ("vacancy.txt", b"content", "text/plain")},
    )
    assert response.status_code == 504
