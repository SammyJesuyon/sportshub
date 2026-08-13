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


def test_follow_rejects_browser_supplied_user_id(client, fan):
    arsenal = search_team(client, "Arsenal")

    response = client.put(
        "/api/v1/users/me/team-preferences",
        headers=fan["headers"],
        json={"userId": "someone-else", "team_ids": [arsenal["id"]]},
    )

    assert response.status_code == 422


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
