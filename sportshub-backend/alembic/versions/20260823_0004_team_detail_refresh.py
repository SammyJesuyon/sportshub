"""Track quota-safe team detail refresh attempts."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260823_0004"
down_revision: Union[str, None] = "20260823_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "teams",
        sa.Column("details_checked_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("teams", "details_checked_at")
