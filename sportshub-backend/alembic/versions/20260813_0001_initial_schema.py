"""Create the initial SportsHub account and preference schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260813_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "teams",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("api_team_id", sa.Integer(), nullable=True),
        sa.Column("third_party_id", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teams_api_team_id", "teams", ["api_team_id"], unique=True)
    op.create_index("ix_teams_third_party_id", "teams", ["third_party_id"], unique=True)
    op.create_index("ix_teams_name", "teams", ["name"], unique=False)

    op.create_table(
        "user_notification_preferences",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("pre_match_reminder", sa.Boolean(), nullable=False),
        sa.Column("match_start", sa.Boolean(), nullable=False),
        sa.Column("match_end", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "user_push_devices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("expo_push_token", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "expo_push_token"),
    )
    op.create_index("ix_user_push_devices_user_id", "user_push_devices", ["user_id"])
    op.create_index("ix_user_push_devices_expo_push_token", "user_push_devices", ["expo_push_token"])

    op.create_table(
        "user_team_preferences",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("team_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "team_id"),
    )
    op.create_index("ix_user_team_preferences_user_id", "user_team_preferences", ["user_id"])
    op.create_index("ix_user_team_preferences_team_id", "user_team_preferences", ["team_id"])


def downgrade() -> None:
    op.drop_table("user_team_preferences")
    op.drop_table("user_push_devices")
    op.drop_table("user_notification_preferences")
    op.drop_table("teams")
    op.drop_table("users")
