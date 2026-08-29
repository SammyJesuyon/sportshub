import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.base import Base
from app.integrations.api_sports import SampleSportsAdapter
from app.integrations.email import RecordingEmailSender
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    integration_database_url = os.getenv("TEST_DATABASE_URL")
    database_path = tmp_path / "sportshub-test.db"
    settings = Settings(
        environment="test",
        database_url=integration_database_url or f"sqlite:///{database_path}",
        secret_key="test-secret-key-that-is-long-enough",
        sports_provider="sample",
        cors_origins="http://testserver",
    )
    app = create_app(
        settings=settings,
        sports_provider=SampleSportsAdapter(),
        email_sender=RecordingEmailSender(),
    )
    engine = app.state.session_factory.kw["bind"]
    if integration_database_url:
        with engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())
    else:
        Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    if integration_database_url:
        with engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())
    else:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def fan(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "fan@example.com",
            "username": "sportsfan",
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    return {
        "user": payload["user"],
        "token": payload["access_token"],
        "headers": {"Authorization": f"Bearer {payload['access_token']}"},
    }
