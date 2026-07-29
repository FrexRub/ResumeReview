"""harden users for authentication

Revision ID: 7f3e2b941c10
Revises: ce3a01b790d1
Create Date: 2026-07-29 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "7f3e2b941c10"
down_revision: Union[str, Sequence[str], None] = "ce3a01b790d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "name",
        existing_type=sa.String(),
        type_=sa.String(length=80),
        existing_nullable=True,
        nullable=False,
    )
    op.alter_column("users", "hashed_password", existing_type=sa.String(), nullable=False)
    op.add_column(
        "users",
        sa.Column("auth_version", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_index("ix_users_name", "users", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_name", table_name="users")
    op.drop_column("users", "auth_version")
    op.alter_column("users", "hashed_password", existing_type=sa.String(), nullable=True)
    op.alter_column(
        "users",
        "name",
        existing_type=sa.String(length=80),
        type_=sa.String(),
        existing_nullable=False,
        nullable=True,
    )
