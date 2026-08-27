from datetime import date, datetime, timezone

import httpx

from app.integrations.api_sports import ProviderFixture, ProviderFixtureTeam
from app.integrations.isports import ISportsAdapter


def test_isports_team_search_uses_query_key_and_normalizes_profile(monkeypatch):
    observed = {}

    def fake_get(client, url, *, params, headers):
        observed.update(url=url, params=params, headers=headers)
        request = httpx.Request("GET", url, params=params, headers=headers)
        return httpx.Response(
            200,
            request=request,
            json={
                "code": 0,
                "message": "success",
                "data": [
                    {
                        "teamId": "42",
                        "leagueId": "39",
                        "name": "Arsenal",
                        "logo": "arsenal.png",
                        "foundingDate": "1886-12-01",
                        "address": "Hornsey Road",
                        "area": "London",
                        "venue": "Emirates Stadium",
                        "capacity": 60260,
                        "isNational": False,
                    }
                ],
            },
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    teams = ISportsAdapter(
        "test-secret",
        "https://api.isportsapi.com/",
        "https://api2.isportsapi.com/",
    ).search_teams("Arsenal")

    assert observed == {
        "url": "https://api.isportsapi.com/sport/football/team/search",
        "params": {"api_key": "test-secret", "name": "Arsenal"},
        "headers": {"Accept": "application/json"},
    }
    assert teams[0].provider_id == 42
    assert teams[0].name == "Arsenal"
    assert teams[0].founded == 1886
    assert teams[0].venue_name == "Emirates Stadium"
    assert teams[0].league_provider_id == 39


def test_isports_team_schedule_filters_team_and_reuses_league_cache(monkeypatch):
    calls = []

    def fake_get(client, url, *, params, headers):
        calls.append((url, params))
        request = httpx.Request("GET", url, params=params, headers=headers)
        return httpx.Response(
            200,
            request=request,
            json={
                "code": 0,
                "message": "success",
                "data": [
                    {
                        "matchId": "9001",
                        "leagueId": "39",
                        "leagueName": "Premier League",
                        "matchTime": 1787252400,
                        "status": 0,
                        "homeId": "42",
                        "homeName": "Arsenal",
                        "awayId": "49",
                        "awayName": "Chelsea",
                    },
                    {
                        "matchId": "9002",
                        "leagueId": "39",
                        "leagueName": "Premier League",
                        "matchTime": 1787338800,
                        "status": 0,
                        "homeId": "50",
                        "homeName": "Manchester City",
                        "awayId": "40",
                        "awayName": "Liverpool",
                    },
                ],
            },
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    adapter = ISportsAdapter("test-secret", "https://api.isportsapi.com")

    first = adapter.team_schedule(42, 39)
    second = adapter.team_schedule(49, 39)

    assert [fixture.fixture_id for fixture in first] == [9001]
    assert [fixture.fixture_id for fixture in second] == [9001]
    assert calls == [
        (
            "https://api.isportsapi.com/sport/football/schedule/basic",
            {"api_key": "test-secret", "leagueId": "39"},
        )
    ]


def test_isports_matchday_uses_date_schedule_and_persistent_cache(monkeypatch, tmp_path):
    calls = []

    def fake_get(client, url, *, params, headers):
        calls.append((url, params))
        request = httpx.Request("GET", url, params=params, headers=headers)
        return httpx.Response(
            200,
            request=request,
            json={
                "code": 0,
                "message": "success",
                "data": [
                    {
                        "matchId": "9001",
                        "leagueId": "39",
                        "leagueName": "Premier League",
                        "matchTime": 1787252400,
                        "status": -1,
                        "homeId": "42",
                        "homeName": "Arsenal",
                        "awayId": "49",
                        "awayName": "Chelsea",
                        "homeScore": 2,
                        "awayScore": 1,
                        "homeHalfScore": 1,
                        "awayHalfScore": 0,
                    }
                ],
            },
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    cache_path = tmp_path / "isports-cache.json"
    selected_date = date(2026, 8, 20)
    first = ISportsAdapter(
        "test-secret",
        "https://api.isportsapi.com",
        cache_path=str(cache_path),
    )
    snapshot = first.matchday_snapshot(selected_date)
    restored = ISportsAdapter(
        "test-secret",
        "https://api.isportsapi.com",
        cache_path=str(cache_path),
    ).matchday_snapshot(selected_date)

    assert snapshot.fixtures[0].fixture_id == 9001
    assert snapshot.fixtures[0].status_short == "FT"
    assert snapshot.fixtures[0].home.goals == 2
    assert restored.cache_hit is True
    assert calls == [
        (
            "https://api.isportsapi.com/sport/football/schedule/basic",
            {"api_key": "test-secret", "date": "2026-08-20"},
        )
    ]


def test_isports_today_uses_live_score_feed(monkeypatch):
    calls = []

    def fake_get(client, url, *, params, headers):
        calls.append((url, params))
        request = httpx.Request("GET", url, params=params, headers=headers)
        return httpx.Response(
            200,
            request=request,
            json={"code": 0, "message": "success", "data": []},
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    ISportsAdapter("test-secret", "https://api.isportsapi.com").matchday_snapshot(
        datetime.now(timezone.utc).date()
    )

    assert calls == [
        (
            "https://api.isportsapi.com/sport/football/livescores",
            {"api_key": "test-secret"},
        )
    ]


def test_isports_fixture_detail_normalizes_events_stats_and_lineups(monkeypatch):
    calls = []
    fixture_id = 9001
    kickoff = datetime.now(timezone.utc).replace(microsecond=0)

    def fake_get(client, url, *, params, headers):
        calls.append((url, params))
        request = httpx.Request("GET", url, params=params, headers=headers)
        if url.endswith("/schedule/basic"):
            data = [
                {
                    "matchId": str(fixture_id),
                    "leagueId": "39",
                    "leagueName": "Premier League",
                    "matchTime": int(kickoff.timestamp()),
                    "status": -1,
                    "homeId": "42",
                    "homeName": "Arsenal",
                    "awayId": "49",
                    "awayName": "Chelsea",
                    "homeScore": 2,
                    "awayScore": 1,
                    "homeHalfScore": 1,
                    "awayHalfScore": 0,
                }
            ]
        elif url.endswith("/events"):
            data = [
                {
                    "matchId": str(fixture_id),
                    "events": [
                        {
                            "minute": "72",
                            "overtime": "0",
                            "type": 1,
                            "homeEvent": True,
                            "playerName": "A. Player (Assist:A. Assist)",
                        }
                    ],
                }
            ]
        elif url.endswith("/stats"):
            data = [
                {
                    "matchId": str(fixture_id),
                    "stats": [
                        {"type": 3, "home": 15, "away": 8},
                        {"type": 14, "home": 58, "away": 42},
                    ],
                }
            ]
        else:
            data = [
                {
                    "matchId": str(fixture_id),
                    "homeFormation": "433",
                    "awayFormation": "4231",
                    "homeLineup": [
                        {"playerId": "1", "name": "A. Keeper", "number": 1, "position": 0}
                    ],
                    "awayLineup": [],
                    "homeBackup": [],
                    "awayBackup": [],
                }
            ]
        return httpx.Response(
            200,
            request=request,
            json={"code": 0, "message": "success", "data": data},
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    fixture = ProviderFixture(
        fixture_id=fixture_id,
        kickoff=kickoff.isoformat(),
        timezone="UTC",
        league_id=39,
        league_name="Premier League",
        league_logo_url=None,
        status_short="FT",
        status_long="Match Finished",
        elapsed=90,
        home=ProviderFixtureTeam(42, "Arsenal", None, 2),
        away=ProviderFixtureTeam(49, "Chelsea", None, 1),
    )
    detail = ISportsAdapter(
        "test-secret", "https://api.isportsapi.com"
    ).fixture_detail(fixture).detail

    assert detail.halftime_home == 1
    assert detail.events[0].team_name == "Arsenal"
    assert detail.events[0].assist_name == "A. Assist"
    assert detail.statistics[0].statistics[1].value == "58%"
    assert detail.lineups[0].formation == "4-3-3"
    assert detail.lineups[0].starting_xi[0].position == "G"
    assert [call[0].rsplit("/", 1)[-1] for call in calls] == [
        "basic",
        "events",
        "stats",
        "lineups",
    ]


def test_isports_uses_secondary_host_after_gateway_failure(monkeypatch):
    calls = []

    def fake_get(client, url, *, params, headers):
        calls.append(url)
        request = httpx.Request("GET", url, params=params, headers=headers)
        if url.startswith("https://api.isportsapi.com"):
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            request=request,
            json={"code": 0, "message": "success", "data": []},
        )

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    result = ISportsAdapter(
        "test-secret",
        "https://api.isportsapi.com",
        "https://api2.isportsapi.com",
    ).search_teams("Arsenal")

    assert result == []
    assert calls == [
        "https://api.isportsapi.com/sport/football/team/search",
        "https://api2.isportsapi.com/sport/football/team/search",
    ]
