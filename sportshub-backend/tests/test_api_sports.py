import httpx
import pytest
from datetime import date

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


def test_api_sports_normalizes_matchday_fixtures(monkeypatch):
    call_count = 0

    def fake_get(client, url, *, params, headers):
        nonlocal call_count
        call_count += 1
        request = httpx.Request("GET", url, params=params, headers=headers)
        return httpx.Response(
            200,
            request=request,
            json={
                "errors": [],
                "response": [
                    {
                        "fixture": {
                            "id": 9001,
                            "date": "2026-08-13T19:00:00+00:00",
                            "timezone": "UTC",
                            "status": {"long": "Second Half", "short": "2H", "elapsed": 72},
                        },
                        "league": {"id": 39, "name": "Premier League", "logo": "league.png"},
                        "teams": {
                            "home": {"id": 42, "name": "Arsenal", "logo": "arsenal.png"},
                            "away": {"id": 49, "name": "Chelsea", "logo": "chelsea.png"},
                        },
                        "goals": {"home": 2, "away": 1},
                    }
                ],
            },
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    adapter = ApiSportsAdapter("secret-key", "https://v3.football.api-sports.io")
    snapshot = adapter.matchday_snapshot(date(2026, 8, 13))
    fixtures = snapshot.fixtures

    assert len(fixtures) == 1
    assert fixtures[0].fixture_id == 9001
    assert fixtures[0].status_short == "2H"
    assert fixtures[0].home.name == "Arsenal"
    assert fixtures[0].home.goals == 2

    cached = adapter.matchday_snapshot(date(2026, 8, 13))
    assert cached.fixtures == fixtures
    assert cached.cache_hit is True
    assert call_count == 1


def test_matchday_cache_survives_adapter_restart(monkeypatch, tmp_path):
    calls = 0

    def fake_get(client, url, *, params, headers):
        nonlocal calls
        calls += 1
        request = httpx.Request("GET", url, params=params, headers=headers)
        return httpx.Response(
            200,
            request=request,
            headers={
                "x-ratelimit-requests-limit": "100",
                "x-ratelimit-requests-remaining": "70",
                "x-ratelimit-limit": "10",
                "x-ratelimit-remaining": "9",
            },
            json={"errors": [], "response": []},
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    cache_path = tmp_path / "provider-cache.json"
    first = ApiSportsAdapter("secret", "https://v3.football.api-sports.io", str(cache_path))
    first.matchday_snapshot(date(2026, 8, 13))

    restored = ApiSportsAdapter("secret", "https://v3.football.api-sports.io", str(cache_path))
    snapshot = restored.matchday_snapshot(date(2026, 8, 13))

    assert snapshot.cache_hit is True
    assert snapshot.quota.daily_remaining == 70
    assert calls == 1


def test_fixture_detail_normalizes_and_persists_statistics_lineups_and_timeline(
    monkeypatch, tmp_path
):
    calls = 0

    def fake_get(client, url, *, params, headers):
        nonlocal calls
        calls += 1
        request = httpx.Request("GET", url, params=params, headers=headers)
        base = {
            "fixture": {
                "id": 9001,
                "date": "2026-08-13T19:00:00+00:00",
                "timezone": "UTC",
                "referee": "A. Referee",
                "venue": {"name": "Emirates Stadium", "city": "London"},
                "status": {"long": "Match Finished", "short": "FT", "elapsed": 90},
            },
            "league": {"id": 39, "name": "Premier League", "logo": "league.png"},
            "teams": {
                "home": {"id": 42, "name": "Arsenal", "logo": "arsenal.png"},
                "away": {"id": 49, "name": "Chelsea", "logo": "chelsea.png"},
            },
            "goals": {"home": 2, "away": 1},
        }
        if "id" in params:
            base.update(
                score={"halftime": {"home": 1, "away": 0}, "fulltime": {"home": 2, "away": 1}},
                events=[{
                    "time": {"elapsed": 72, "extra": None},
                    "team": {"name": "Arsenal"},
                    "player": {"name": "A. Player"},
                    "assist": {"name": "A. Assist"},
                    "type": "Goal",
                    "detail": "Normal Goal",
                }],
                statistics=[
                    {"team": {"id": 42, "name": "Arsenal", "logo": "arsenal.png"}, "statistics": [{"type": "Ball Possession", "value": "58%"}, {"type": "Shots on Goal", "value": 7}]},
                    {"team": {"id": 49, "name": "Chelsea", "logo": "chelsea.png"}, "statistics": [{"type": "Ball Possession", "value": "42%"}, {"type": "Shots on Goal", "value": 3}]},
                ],
                lineups=[{
                    "team": {"id": 42, "name": "Arsenal", "logo": "arsenal.png"},
                    "formation": "4-3-3",
                    "coach": {"name": "M. Coach"},
                    "startXI": [{"player": {"id": 1, "name": "A. Keeper", "number": 1, "pos": "G", "grid": "1:1"}}],
                    "substitutes": [{"player": {"id": 2, "name": "A. Substitute", "number": 12, "pos": "D", "grid": None}}],
                }],
            )
        return httpx.Response(200, request=request, json={"errors": [], "response": [base]})

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    cache_path = tmp_path / "provider-cache.json"
    adapter = ApiSportsAdapter(
        "secret-key", "https://v3.football.api-sports.io", str(cache_path)
    )
    fixture = adapter.matchday_snapshot(date(2026, 8, 13)).fixtures[0]
    detail = adapter.fixture_detail(fixture).detail
    restored = ApiSportsAdapter(
        "secret-key", "https://v3.football.api-sports.io", str(cache_path)
    )
    cached = restored.fixture_detail(fixture)

    assert detail.events[0].detail == "Normal Goal"
    assert detail.statistics[0].statistics[1].value == "7"
    assert detail.lineups[0].formation == "4-3-3"
    assert detail.lineups[0].starting_xi[0].name == "A. Keeper"
    assert cached.cache_hit is True
    assert calls == 2
