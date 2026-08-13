def search_team(client, query):
    response = client.get("/api/v1/teams/", params={"search": query})
    assert response.status_code == 200
    assert response.json()
    return response.json()[0]


def test_provider_failure_is_a_controlled_service_unavailable(client):
    import httpx

    class FailingProvider:
        def search_teams(self, query):
            raise httpx.ConnectError("provider unavailable")

    original = client.app.state.sports_provider
    client.app.state.sports_provider = FailingProvider()
    try:
        response = client.get("/api/v1/teams/", params={"search": "unseen team"})
    finally:
        client.app.state.sports_provider = original

    assert response.status_code == 503
    assert response.json()["detail"] == "Sports provider is temporarily unavailable"


def test_search_warms_stable_team_ids(client):
    first = search_team(client, "Arsenal")
    second = search_team(client, "Arsenal")

    assert first["id"] == second["id"]
    assert first["api_team_id"] == 42
    assert first["name"] == "Arsenal"


def test_follow_team_derives_current_user_and_tracks_duplicates(client, fan):
    arsenal = search_team(client, "Arsenal")

    first = client.put(
        "/api/v1/users/me/team-preferences",
        headers=fan["headers"],
        json={"team_ids": [arsenal["api_team_id"]]},
    )
    second = client.put(
        "/api/v1/users/me/team-preferences",
        headers=fan["headers"],
        json={"team_ids": [arsenal["id"]]},
    )

    assert first.status_code == 200
    assert first.json()["added_count"] == 1
    assert first.json()["duplicate_count"] == 0
    assert second.status_code == 200
    assert second.json()["added_count"] == 0
    assert second.json()["duplicate_count"] == 1

    followed = client.get(
        "/api/v1/users/me/team-preferences", headers=fan["headers"]
    )
    assert followed.status_code == 200
    assert [team["name"] for team in followed.json()] == ["Arsenal"]

    inbox = client.get("/api/v1/notifications/inbox", headers=fan["headers"])
    assert inbox.status_code == 200
    assert inbox.json()["unread_count"] == 2
    assert [item["kind"] for item in inbox.json()["items"]] == [
        "team_followed",
        "welcome",
    ]


def test_follow_rejects_browser_supplied_user_id(client, fan):
    arsenal = search_team(client, "Arsenal")

    response = client.put(
        "/api/v1/users/me/team-preferences",
        headers=fan["headers"],
        json={"userId": "someone-else", "team_ids": [arsenal["id"]]},
    )

    assert response.status_code == 422


def test_remove_team_only_deletes_current_users_association(client, fan):
    arsenal = search_team(client, "Arsenal")
    client.put(
        "/api/v1/users/me/team-preferences",
        headers=fan["headers"],
        json={"team_ids": [arsenal["id"]]},
    )
    outsider = client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "username": "otherfan",
            "password": "SecurePass123!",
        },
    ).json()
    outsider_headers = {"Authorization": f"Bearer {outsider['access_token']}"}
    client.put(
        "/api/v1/users/me/team-preferences",
        headers=outsider_headers,
        json={"team_ids": [arsenal["id"]]},
    )

    removed = client.delete(
        f"/api/v1/users/me/team-preferences/{arsenal['id']}",
        headers=fan["headers"],
    )
    repeated = client.delete(
        f"/api/v1/users/me/team-preferences/{arsenal['id']}",
        headers=fan["headers"],
    )

    assert removed.status_code == 200
    assert removed.json()["name"] == "Arsenal"
    assert client.get(
        "/api/v1/users/me/team-preferences", headers=fan["headers"]
    ).json() == []
    assert [team["name"] for team in client.get(
        "/api/v1/users/me/team-preferences", headers=outsider_headers
    ).json()] == ["Arsenal"]
    assert search_team(client, "Arsenal")["id"] == arsenal["id"]
    assert repeated.status_code == 404


def test_remove_team_requires_authentication(client):
    response = client.delete("/api/v1/users/me/team-preferences/team-1")
    assert response.status_code == 401


def test_unresolved_team_returns_not_found(client, fan):
    response = client.put(
        "/api/v1/users/me/team-preferences",
        headers=fan["headers"],
        json={"team_ids": [999999]},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["not_found_ids"] == ["999999"]


def test_global_notification_preferences_are_a_separate_transaction(client, fan):
    arsenal = search_team(client, "Arsenal")
    followed = client.put(
        "/api/v1/users/me/team-preferences",
        headers=fan["headers"],
        json={"team_ids": [arsenal["id"]]},
    )
    assert followed.status_code == 200

    invalid_preferences = client.put(
        "/api/v1/notifications/preferences",
        headers=fan["headers"],
        json={"enabled": "not-a-boolean"},
    )
    assert invalid_preferences.status_code == 422

    still_followed = client.get(
        "/api/v1/users/me/team-preferences", headers=fan["headers"]
    )
    assert [team["name"] for team in still_followed.json()] == ["Arsenal"]


def test_notification_defaults_and_partial_update(client, fan):
    defaults = client.get(
        "/api/v1/notifications/preferences", headers=fan["headers"]
    )
    assert defaults.status_code == 200
    assert defaults.json() == {
        "enabled": True,
        "pre_match_reminder": True,
        "match_start": True,
        "match_end": True,
    }

    updated = client.put(
        "/api/v1/notifications/preferences",
        headers=fan["headers"],
        json={"match_end": False},
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is True
    assert updated.json()["match_start"] is True
    assert updated.json()["match_end"] is False


def test_notification_update_rejects_per_team_rules_and_user_id(client, fan):
    response = client.put(
        "/api/v1/notifications/preferences",
        headers=fan["headers"],
        json={
            "userId": "someone-else",
            "teamId": "team-1",
            "eventTypes": ["goal"],
            "enabled": True,
        },
    )

    assert response.status_code == 422


def test_register_expo_device_is_idempotent(client, fan):
    token = "ExponentPushToken[sportshub-test-device]"
    first = client.post(
        "/api/v1/notifications/devices",
        headers=fan["headers"],
        json={"expo_push_token": token},
    )
    second = client.post(
        "/api/v1/notifications/devices",
        headers=fan["headers"],
        json={"expo_push_token": token},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["is_active"] is True


def test_alert_inbox_is_user_scoped_and_supports_read_state(client, fan):
    inbox = client.get("/api/v1/notifications/inbox", headers=fan["headers"])
    alert = inbox.json()["items"][0]

    marked = client.put(
        f"/api/v1/notifications/inbox/{alert['id']}/read",
        headers=fan["headers"],
    )
    after_mark = client.get("/api/v1/notifications/inbox", headers=fan["headers"])
    mark_all = client.put(
        "/api/v1/notifications/inbox/read-all", headers=fan["headers"]
    )

    assert inbox.status_code == 200
    assert inbox.json()["unread_count"] == 1
    assert marked.status_code == 200
    assert marked.json()["is_read"] is True
    assert after_mark.json()["unread_count"] == 0
    assert mark_all.json() == {"updated_count": 0}


def test_alert_inbox_requires_authentication_and_hides_other_users_alerts(client, fan):
    outsider = client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "username": "otherfan",
            "password": "SecurePass123!",
        },
    ).json()
    fan_inbox = client.get(
        "/api/v1/notifications/inbox", headers=fan["headers"]
    ).json()
    fan_alert_id = fan_inbox["items"][0]["id"]

    unauthenticated = client.get("/api/v1/notifications/inbox")
    hidden = client.put(
        f"/api/v1/notifications/inbox/{fan_alert_id}/read",
        headers={"Authorization": f"Bearer {outsider['access_token']}"},
    )

    assert unauthenticated.status_code == 401
    assert hidden.status_code == 404
