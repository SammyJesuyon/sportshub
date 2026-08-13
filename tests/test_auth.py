def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "sportshub-api"}


def test_register_authenticate_and_login(client):
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "SAMSON@example.com",
            "username": "samson",
            "password": "SecurePass123!",
        },
    )

    assert registration.status_code == 201
    registered = registration.json()
    assert registered["user"]["email"] == "samson@example.com"
    assert registered["user"]["role"] == "fan"

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {registered['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["id"] == registered["user"]["id"]

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "samson@example.com", "password": "SecurePass123!"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["id"] == registered["user"]["id"]


def test_duplicate_registration_and_invalid_login_are_rejected(client, fan):
    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": "fan@example.com",
            "username": "different",
            "password": "SecurePass123!",
        },
    )
    assert duplicate.status_code == 409

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "fan@example.com", "password": "wrong-password"},
    )
    assert login.status_code == 401


def test_authenticated_endpoint_requires_valid_bearer_token(client):
    missing = client.get("/api/v1/auth/me")
    invalid = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-token"}
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401


def test_production_rejects_default_secret():
    import pytest

    from app.core.config import Settings
    from app.main import create_app

    settings = Settings(environment="production", secret_key="development-only-change-me")
    with pytest.raises(ValueError, match="SECRET_KEY"):
        create_app(settings)
