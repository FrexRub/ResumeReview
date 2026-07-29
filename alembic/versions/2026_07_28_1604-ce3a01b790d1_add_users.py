"""reserve revision for initial user data

Revision ID: ce3a01b790d1
Revises: 3b4e8b9ed622
Create Date: 2026-07-28 16:04:27.103675

Accounts are provisioned manually in Supabase. No default password is committed.
"""

from typing import Sequence, Union

revision: str = "ce3a01b790d1"
down_revision: Union[str, Sequence[str], None] = "3b4e8b9ed622"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
