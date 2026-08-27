"""Store the provider league used to resolve a team's current schedule."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260825_0005"
down_revision: Union[str, None] = "20260823_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "teams",
        sa.Column("league_provider_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_teams_league_provider_id"),
        "teams",
        ["league_provider_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_teams_league_provider_id"), table_name="teams")
    op.drop_column("teams", "league_provider_id")
