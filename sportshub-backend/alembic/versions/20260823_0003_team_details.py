"""Add cached team and venue discovery details."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260823_0003"
down_revision: Union[str, None] = "20260813_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("teams", sa.Column("code", sa.String(length=20), nullable=True))
    op.add_column("teams", sa.Column("founded", sa.Integer(), nullable=True))
    op.add_column("teams", sa.Column("national", sa.Boolean(), nullable=True))
    op.add_column("teams", sa.Column("venue_name", sa.String(length=160), nullable=True))
    op.add_column("teams", sa.Column("venue_address", sa.String(length=240), nullable=True))
    op.add_column("teams", sa.Column("venue_city", sa.String(length=120), nullable=True))
    op.add_column("teams", sa.Column("venue_capacity", sa.Integer(), nullable=True))
    op.add_column("teams", sa.Column("venue_surface", sa.String(length=80), nullable=True))
    op.add_column("teams", sa.Column("venue_image_url", sa.String(length=500), nullable=True))
    op.add_column(
        "teams",
        sa.Column(
            "details_loaded",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("teams", "details_loaded")
    op.drop_column("teams", "venue_image_url")
    op.drop_column("teams", "venue_surface")
    op.drop_column("teams", "venue_capacity")
    op.drop_column("teams", "venue_city")
    op.drop_column("teams", "venue_address")
    op.drop_column("teams", "venue_name")
    op.drop_column("teams", "national")
    op.drop_column("teams", "founded")
    op.drop_column("teams", "code")
