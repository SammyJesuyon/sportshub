import httpx
import pytest

from app.integrations.api_sports import ApiSportsAdapter


def test_api_sports_team_search_uses_expected_url_and_secret_header(monkeypatch):
    observed = {}

    def fake_get(client, url, *, params, headers):
        observed.update(url=url, params=params, headers=headers)
        request = httpx.Request("GET", url, params=params, headers=headers)
        return httpx.Response(
            200,
            request=request,
            json={
                "errors": [],
                "response": [
                    {
                        "team": {
                            "id": 42,
                            "name": "Arsenal",
                            "country": "England",
                            "logo": "https://media.api-sports.io/football/teams/42.png",
                        }
                    }
                ],
            },
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    teams = ApiSportsAdapter("secret-key", "https://v3.football.api-sports.io/").search_teams(
        "Arsenal"
    )

    assert observed == {
        "url": "https://v3.football.api-sports.io/teams",
        "params": {"search": "Arsenal"},
        "headers": {"x-apisports-key": "secret-key"},
    }
    assert [(team.provider_id, team.name, team.country) for team in teams] == [
        (42, "Arsenal", "England")
    ]


def test_api_sports_error_envelope_is_not_treated_as_empty_results(monkeypatch):
    def fake_get(client, url, *, params, headers):
        request = httpx.Request("GET", url, params=params, headers=headers)
        return httpx.Response(
            200,
            request=request,
            json={"errors": {"token": "Invalid key"}, "response": []},
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    with pytest.raises(ValueError, match="rejected"):
        ApiSportsAdapter("invalid-key", "https://v3.football.api-sports.io").search_teams(
            "Arsenal"
        )
