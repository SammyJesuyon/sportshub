from urllib.parse import parse_qs, urlparse


def latest_email_token(client) -> str:
    message = client.app.state.email_sender.messages[-1]
    verification_line = next(
        line for line in message.text.splitlines() if line.startswith("Verify email: ")
    )
    verification_url = verification_line.removeprefix("Verify email: ")
    return parse_qs(urlparse(verification_url).query)["token"][0]


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "sportshub-api"}

    readiness = client.get("/health/ready")
    assert readiness.status_code == 200
    assert readiness.json() == {"status": "ready", "database": "connected"}


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
    assert registered["user"]["email_verified"] is False
    assert registered["user"]["pending_email"] is None
    assert registered["user"]["role"] == "fan"
    assert client.app.state.email_sender.messages[-1].recipient == "samson@example.com"

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


def test_authenticated_user_can_update_profile(client, fan):
    response = client.patch(
        "/api/v1/users/me",
        headers=fan["headers"],
        json={"email": "UPDATED@example.com", "username": "updated_fan"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "fan@example.com"
    assert response.json()["pending_email"] == "updated@example.com"
    assert response.json()["username"] == "updated_fan"

    previous_login_before_verification = client.post(
        "/api/v1/auth/login",
        json={"email": "fan@example.com", "password": "SecurePass123!"},
    )
    updated_login_before_verification = client.post(
        "/api/v1/auth/login",
        json={"email": "updated@example.com", "password": "SecurePass123!"},
    )
    assert previous_login_before_verification.status_code == 200
    assert updated_login_before_verification.status_code == 401

    verification = client.post(
        "/api/v1/auth/verify-email",
        json={"token": latest_email_token(client)},
    )
    assert verification.status_code == 200
    assert verification.json()["email"] == "updated@example.com"
    assert verification.json()["pending_email"] is None
    assert verification.json()["email_verified"] is True

    previous_login = client.post(
        "/api/v1/auth/login",
        json={"email": "fan@example.com", "password": "SecurePass123!"},
    )
    updated_login = client.post(
        "/api/v1/auth/login",
        json={"email": "updated@example.com", "password": "SecurePass123!"},
    )
    assert previous_login.status_code == 401
    assert updated_login.status_code == 200


def test_profile_update_rejects_another_users_identity(client, fan):
    other = client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "username": "other_fan",
            "password": "SecurePass123!",
        },
    )
    assert other.status_code == 201

    response = client.patch(
        "/api/v1/users/me",
        headers=fan["headers"],
        json={"email": "other@example.com", "username": "other_fan"},
    )
    assert response.status_code == 409


def test_account_deletion_requires_password_and_invalidates_identity(client, fan):
    rejected = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=fan["headers"],
        json={"password": "WrongPass123!"},
    )
    assert rejected.status_code == 403

    deleted = client.request(
        "DELETE",
        "/api/v1/users/me",
        headers=fan["headers"],
        json={"password": "SecurePass123!"},
    )
    assert deleted.status_code == 204
    assert deleted.content == b""

    me = client.get("/api/v1/auth/me", headers=fan["headers"])
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "fan@example.com", "password": "SecurePass123!"},
    )
    assert me.status_code == 401
    assert login.status_code == 401


def test_registration_email_can_be_verified_and_resent(client, fan):
    verification = client.post(
        "/api/v1/auth/verify-email",
        json={"token": latest_email_token(client)},
    )
    assert verification.status_code == 200
    assert verification.json()["email_verified"] is True

    already_verified = client.post(
        "/api/v1/users/me/email-verification", headers=fan["headers"]
    )
    assert already_verified.status_code == 400

    second_registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "unverified@example.com",
            "username": "unverified_fan",
            "password": "SecurePass123!",
        },
    )
    resend = client.post(
        "/api/v1/users/me/email-verification",
        headers={
            "Authorization": f"Bearer {second_registration.json()['access_token']}"
        },
    )
    assert resend.status_code == 202
    assert client.app.state.email_sender.messages[-1].recipient == "unverified@example.com"


def test_authenticated_user_can_change_password(client, fan):
    wrong_current_password = client.put(
        "/api/v1/users/me/password",
        headers=fan["headers"],
        json={
            "current_password": "WrongPass123!",
            "new_password": "NewSecurePass123!",
        },
    )
    assert wrong_current_password.status_code == 403

    unchanged = client.put(
        "/api/v1/users/me/password",
        headers=fan["headers"],
        json={
            "current_password": "SecurePass123!",
            "new_password": "SecurePass123!",
        },
    )
    assert unchanged.status_code == 400

    changed = client.put(
        "/api/v1/users/me/password",
        headers=fan["headers"],
        json={
            "current_password": "SecurePass123!",
            "new_password": "NewSecurePass123!",
        },
    )
    assert changed.status_code == 204
    assert client.app.state.email_sender.messages[-1].subject == (
        "Your SportsHub password was changed"
    )

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "fan@example.com", "password": "SecurePass123!"},
    )
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "fan@example.com", "password": "NewSecurePass123!"},
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_production_rejects_default_secret():
    import pytest

    from app.core.config import Settings
    from app.main import create_app

    settings = Settings(environment="production", secret_key="development-only-change-me")
    with pytest.raises(ValueError, match="SECRET_KEY"):
        create_app(settings)
