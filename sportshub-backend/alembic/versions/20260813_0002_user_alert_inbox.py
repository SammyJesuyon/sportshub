"""Add persisted in-app alert inbox records."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260813_0002"
down_revision: Union[str, None] = "20260813_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_alerts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("link_url", sa.String(length=500), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_alerts_user_id", "user_alerts", ["user_id"])
    op.create_index("ix_user_alerts_is_read", "user_alerts", ["is_read"])
    op.create_index("ix_user_alerts_created_at", "user_alerts", ["created_at"])


def downgrade() -> None:
    op.drop_table("user_alerts")
