from alembic import command
from alembic.config import Config
from sqlalchemy import inspect


def test_initial_migration_creates_and_removes_schema(tmp_path, monkeypatch):
    database_path = tmp_path / "migration-test.db"
    database_url = f"sqlite:///{database_path}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    from app.core.config import get_settings

    get_settings.cache_clear()
    config = Config("alembic.ini")
    command.upgrade(config, "head")

    from sqlalchemy import create_engine

    engine = create_engine(database_url)
    assert set(inspect(engine).get_table_names()) >= {
        "alembic_version",
        "users",
        "teams",
        "user_team_preferences",
        "user_notification_preferences",
        "user_push_devices",
    }

    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    get_settings.cache_clear()
