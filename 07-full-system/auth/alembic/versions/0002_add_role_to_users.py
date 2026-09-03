"""add role to users

Revision ID: 0002_add_role
Revises: 41e950ad0c34
Create Date: 2026-02-10

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_role"
down_revision: Union[str, Sequence[str], None] = "41e950ad0c34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
