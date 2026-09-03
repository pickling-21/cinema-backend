"""init

Revision ID: 41e950ad0c34
Revises:
Create Date: 2026-02-04 23:13:01.751054

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "41e950ad0c34"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("login", sa.String(255), unique=True, nullable=False),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(50)),
        sa.Column("last_name", sa.String(50)),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), default=False),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("users")
