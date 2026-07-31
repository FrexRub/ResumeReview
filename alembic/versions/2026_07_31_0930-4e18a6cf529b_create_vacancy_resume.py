"""create vacancy_resume table

Revision ID: 4e18a6cf529b
Revises: b8d172394de1
Create Date: 2026-07-31 09:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4e18a6cf529b"
down_revision: str | Sequence[str] | None = "b8d172394de1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vacancy_resume",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("title_vacancy", sa.Text(), nullable=True),
        sa.Column("desired_position", sa.Text(), nullable=True),
        sa.Column("summary_resume", sa.Text(), nullable=True),
        sa.Column("score_label", sa.Text(), nullable=True),
        sa.Column("candidate_rating", sa.Integer(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("recommendation_reason", sa.Text(), nullable=True),
        sa.Column("executive_summary", sa.Text(), nullable=True),
        sa.Column("short_conclusion", sa.Text(), nullable=True),
        sa.Column("url_resume", sa.Text(), nullable=True),
        sa.Column("viewed", sa.Boolean(), server_default=sa.false(), nullable=False),        
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("vacancy_resume")
