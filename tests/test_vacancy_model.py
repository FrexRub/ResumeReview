from sqlalchemy import BigInteger, Boolean, DateTime, Text

from src.models import Base, Vacancy


def test_vacancy_model_matches_vacancies_table() -> None:
    table = Vacancy.__table__

    assert table.name == "vacancys"
    assert table is Base.metadata.tables["vacancys"]
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert isinstance(table.c.id.type, BigInteger)
    assert table.c.id.identity is not None

    assert set(table.columns.keys()) == {
        "id",
        "created_at",
        "content",
        "is_active",
    }
    assert isinstance(table.c.created_at.type, DateTime)
    assert table.c.created_at.type.timezone is True
    assert table.c.created_at.server_default is not None
    assert isinstance(table.c.content.type, Text)
    assert isinstance(table.c.is_active.type, Boolean)
    assert table.c.is_active.server_default is not None

    assert all(not column.nullable for column in table.columns)
