from sqlalchemy import BigInteger, DateTime, Text

from src.models.resume_review_status import ResumeReviewStatus


def test_resume_review_status_matches_existing_supabase_table() -> None:
    table = ResumeReviewStatus.__table__

    assert table.name == "my_ResumeReviewStatus"
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert isinstance(table.c.id.type, BigInteger)
    assert table.c.id.identity is not None

    expected_columns = {
        "id",
        "channel",
        "id_message",
        "date_message",
        "sender",
        "topic_messag",
        "status",
        "type_messag",
    }
    assert set(table.columns.keys()) == expected_columns
    assert isinstance(table.c.channel.type, Text)
    assert isinstance(table.c.id_message.type, Text)
    assert isinstance(table.c.date_message.type, DateTime)
    assert table.c.date_message.type.timezone is True
    assert table.c.status.server_default is not None

    nullable_columns = {column.name for column in table.columns if column.nullable}
    assert nullable_columns == {"sender", "topic_messag", "type_messag"}

    assert any(
        index.name == "ResumeReviewStatus_channel_ID_message_key"
        and index.unique
        and [column.name for column in index.columns] == ["channel", "id_message"]
        for index in table.indexes
    )
