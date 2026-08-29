"""Add account email verification state."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260828_0006"
down_revision: Union[str, None] = "20260825_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("pending_email", sa.String(length=320), nullable=True)
    )
    op.add_column(
        "users", sa.Column("email_verified_at", sa.DateTime(), nullable=True)
    )
    op.create_index(
        op.f("ix_users_pending_email"),
        "users",
        ["pending_email"],
        unique=True,
    )
    op.execute("UPDATE users SET email_verified_at = created_at")


def downgrade() -> None:
    op.drop_index(op.f("ix_users_pending_email"), table_name="users")
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "pending_email")
