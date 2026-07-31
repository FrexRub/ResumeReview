from sqlalchemy import Boolean, Text

from src.models import Base, VacancyResume


def test_vacancy_resume_model_matches_table() -> None:
    table = VacancyResume.__table__

    assert table.name == "vacancy_resume"
    assert table is Base.metadata.tables["vacancy_resume"]
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert table.c.id.identity is not None

    expected_text_columns = {
        "title_vacancy",
        "desired_position",
        "summary_resume",
        "score_label",
        "candidate_rating",
        "recommendation",
        "recommendation_reason",
        "executive_summary",
        "short_conclusion",
        "url_resume",
    }
    assert set(table.columns.keys()) == {"id", "viewed", *expected_text_columns}
    assert all(
        isinstance(table.c[column_name].type, Text)
        for column_name in expected_text_columns
    )
    assert not table.c.id.nullable
    assert all(table.c[column_name].nullable for column_name in expected_text_columns)
    assert isinstance(table.c.viewed.type, Boolean)
    assert not table.c.viewed.nullable
    assert table.c.viewed.default is not None
    assert table.c.viewed.default.arg is False
    assert table.c.viewed.server_default is not None
