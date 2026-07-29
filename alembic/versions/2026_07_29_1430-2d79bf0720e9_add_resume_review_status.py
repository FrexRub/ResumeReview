"""add ResumeReview email processing status

Revision ID: 2d79bf0720e9
Revises: 7f3e2b941c10
Create Date: 2026-07-29 14:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.engine import Connection

revision: str = "2d79bf0720e9"
down_revision: str | Sequence[str] | None = "7f3e2b941c10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "public"
TABLE_NAME = "my_ResumeReviewStatus"
CREATED_TABLE_COMMENT = "Created by Alembic revision 2d79bf0720e9"
UNIQUE_INDEX_NAME = "ResumeReviewStatus_channel_ID_message_key"


def _create_table() -> None:
    op.create_table(
        TABLE_NAME,
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=False),
            nullable=False,
        ),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("id_message", sa.Text(), nullable=False),
        sa.Column(
            "date_message",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("sender", sa.Text(), nullable=True),
        sa.Column("topic_messag", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Text(),
            server_default=sa.text("'new'::text"),
            nullable=False,
        ),
        sa.Column("type_messag", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="my_ResumeReviewStatus_pkey"),
        schema=SCHEMA,
        comment=CREATED_TABLE_COMMENT,
    )
    op.create_index(
        UNIQUE_INDEX_NAME,
        TABLE_NAME,
        ["channel", "id_message"],
        unique=True,
        schema=SCHEMA,
    )


def _validate_existing_table(bind: Connection) -> None:
    inspector = sa.inspect(bind)
    columns = {
        column["name"]: column
        for column in inspector.get_columns(TABLE_NAME, schema=SCHEMA)
    }
    expected_columns: dict[str, tuple[type[sa.types.TypeEngine], bool]] = {
        "id": (sa.BigInteger, False),
        "channel": (sa.Text, False),
        "id_message": (sa.Text, False),
        "date_message": (sa.DateTime, False),
        "sender": (sa.Text, True),
        "topic_messag": (sa.Text, True),
        "status": (sa.Text, False),
        "type_messag": (sa.Text, True),
    }

    problems: list[str] = []
    missing = expected_columns.keys() - columns.keys()
    unexpected = columns.keys() - expected_columns.keys()
    if missing:
        problems.append(f"missing columns: {sorted(missing)}")
    if unexpected:
        problems.append(f"unexpected columns: {sorted(unexpected)}")

    for name, (expected_type, expected_nullable) in expected_columns.items():
        column = columns.get(name)
        if column is None:
            continue
        if not isinstance(column["type"], expected_type):
            problems.append(
                f"{name} has type {column['type']!s}, "
                f"expected {expected_type.__name__}"
            )
        if column["nullable"] is not expected_nullable:
            problems.append(
                f"{name} nullable={column['nullable']}, "
                f"expected {expected_nullable}"
            )

    id_column = columns.get("id")
    if id_column is not None and not id_column.get("identity"):
        problems.append("id is not an identity column")

    primary_key = inspector.get_pk_constraint(TABLE_NAME, schema=SCHEMA)
    if primary_key.get("constrained_columns") != ["id"]:
        problems.append("primary key is not exactly (id)")

    indexes = inspector.get_indexes(TABLE_NAME, schema=SCHEMA)
    has_unique_message_index = any(
        index.get("unique") and index.get("column_names") == ["channel", "id_message"]
        for index in indexes
    )
    if not has_unique_message_index:
        problems.append("missing unique index on (channel, id_message)")

    if problems:
        details = "; ".join(problems)
        raise RuntimeError(
            f'Existing table {SCHEMA}."{TABLE_NAME}" is incompatible: {details}'
        )


def upgrade() -> None:
    if context.is_offline_mode():
        _create_table()
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table(TABLE_NAME, schema=SCHEMA):
        _validate_existing_table(bind)
        return

    _create_table()


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_table(TABLE_NAME, schema=SCHEMA)
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(TABLE_NAME, schema=SCHEMA):
        return

    table_comment = inspector.get_table_comment(TABLE_NAME, schema=SCHEMA).get("text")
    if table_comment == CREATED_TABLE_COMMENT:
        op.drop_table(TABLE_NAME, schema=SCHEMA)
