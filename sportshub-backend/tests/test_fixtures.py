from datetime import date

from app.integrations.api_sports import (
    ProviderFixture,
    ProviderFixtureDetail,
    ProviderFixtureDetailSnapshot,
    ProviderFixtureEvent,
    ProviderFixtureStatistic,
    ProviderFixtureTeam,
    ProviderLineupPlayer,
    ProviderMatchdaySnapshot,
    ProviderOperationalStatus,
    ProviderQuota,
    ProviderTeamLineup,
    ProviderTeamStatistics,
)
from app.api.fixtures import fixture_is_on_local_date, local_matchday_utc_dates
from app.db.models import User
from zoneinfo import ZoneInfo


def fixture(fixture_id: int, status: str, elapsed=None):
    return ProviderFixture(
        fixture_id=fixture_id,
        kickoff="2026-08-13T19:00:00+00:00",
        timezone="UTC",
        league_id=39,
        league_name="Premier League",
        league_logo_url=None,
        status_short=status,
        status_long=status,
        elapsed=elapsed,
        home=ProviderFixtureTeam(42, "Arsenal", None, 2),
        away=ProviderFixtureTeam(49, "Chelsea", None, 1),
    )


def snapshot(fixtures):
    return ProviderMatchdaySnapshot(
        fixtures=fixtures,
        cache_hit=True,
        cache_age_seconds=12,
        cache_ttl_seconds=300,
        quota=ProviderQuota(100, 71, 10, 9, "2026-08-13T20:00:00+00:00"),
    )


class MatchdayProvider:
    def search_teams(self, query):
        return []

    def matchday_snapshot(self, fixture_date: date):
        assert fixture_date in {date(2026, 8, 13), date(2026, 8, 14)}
        return snapshot(
            [
                fixture(4, "NS"),
                fixture(3, "FT", 90),
                fixture(2, "HT", 45),
                fixture(1, "2H", 72),
            ]
        )

    def fixture_detail(self, selected):
        detail = ProviderFixtureDetail(
            fixture=selected,
            referee="A. Referee",
            venue_name="Emirates Stadium",
            venue_city="London",
            halftime_home=1,
            halftime_away=0,
            fulltime_home=2,
            fulltime_away=1,
            extratime_home=None,
            extratime_away=None,
            penalty_home=None,
            penalty_away=None,
            events=[ProviderFixtureEvent(72, None, "Arsenal", "A. Player", None, "Goal", "Normal Goal")],
            statistics=[
                ProviderTeamStatistics(
                    42,
                    "Arsenal",
                    None,
                    [
                        ProviderFixtureStatistic("Ball Possession", "58%"),
                        ProviderFixtureStatistic("Shots on Goal", "7"),
                    ],
                ),
                ProviderTeamStatistics(
                    49,
                    "Chelsea",
                    None,
                    [
                        ProviderFixtureStatistic("Ball Possession", "42%"),
                        ProviderFixtureStatistic("Shots on Goal", "3"),
                    ],
                ),
            ],
            lineups=[
                ProviderTeamLineup(
                    42,
                    "Arsenal",
                    None,
                    "4-3-3",
                    "M. Coach",
                    [ProviderLineupPlayer(1, "A. Keeper", 1, "G", "1:1")],
                    [ProviderLineupPlayer(2, "A. Substitute", 12, "D", None)],
                )
            ],
        )
        return ProviderFixtureDetailSnapshot(
            detail=detail,
            cache_hit=False,
            cache_age_seconds=0,
            cache_ttl_seconds=300,
            quota=ProviderQuota(100, 70, 10, 8, "2026-08-13T20:00:01+00:00"),
        )

    def operational_status(self):
        return ProviderOperationalStatus(
            quota=ProviderQuota(100, 70, 10, 8, "2026-08-13T20:00:01+00:00"),
            matchday_cache_entries=1,
            fixture_detail_cache_entries=1,
            persistent_cache_enabled=True,
        )


def test_matchday_paginates_without_exposing_operational_metadata(client):
    original = client.app.state.sports_provider
    client.app.state.sports_provider = MatchdayProvider()
    try:
        response = client.get(
            "/api/v1/fixtures/matchday?date=2026-08-13&timezone=America%2FChicago&page=1&page_size=2"
        )
        live = client.get(
            "/api/v1/fixtures/matchday?date=2026-08-13&bucket=live&page=1&page_size=12"
        )
    finally:
        client.app.state.sports_provider = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_items"] == 4
    assert payload["timezone"] == "America/Chicago"
    assert payload["total_pages"] == 2
    assert len(payload["fixtures"]) == 2
    assert payload["counts"] == {
        "live": 1,
        "half_time": 1,
        "full_time": 1,
        "scheduled": 1,
    }
    assert "cache" not in payload
    assert "quota" not in payload
    assert [item["bucket"] for item in live.json()["fixtures"]] == ["live"]


def test_live_matches_are_sorted_by_latest_kickoff_first(client):
    class LiveOrderingProvider(MatchdayProvider):
        def matchday_snapshot(self, fixture_date):
            earlier = ProviderFixture(
                **{
                    **fixture(201, "2H", 70).__dict__,
                    "kickoff": "2026-08-13T18:00:00+00:00",
                }
            )
            latest = ProviderFixture(
                **{
                    **fixture(202, "1H", 10).__dict__,
                    "kickoff": "2026-08-13T20:00:00+00:00",
                }
            )
            return snapshot([earlier, latest])

    original = client.app.state.sports_provider
    client.app.state.sports_provider = LiveOrderingProvider()
    try:
        response = client.get(
            "/api/v1/fixtures/matchday?date=2026-08-13&timezone=UTC&bucket=live"
        )
    finally:
        client.app.state.sports_provider = original

    assert response.status_code == 200
    assert [item["fixture_id"] for item in response.json()["fixtures"]] == [202, 201]


def test_fixture_detail_returns_timeline_statistics_and_lineups(client):
    original = client.app.state.sports_provider
    client.app.state.sports_provider = MatchdayProvider()
    try:
        response = client.get(
            "/api/v1/fixtures/1?date=2026-08-13&timezone=America%2FChicago"
        )
    finally:
        client.app.state.sports_provider = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["fixture"]["fixture_id"] == 1
    assert payload["fixture"]["kickoff"] == "2026-08-13T14:00:00-05:00"
    assert payload["fixture"]["timezone"] == "America/Chicago"
    assert payload["venue_name"] == "Emirates Stadium"
    assert payload["events"][0]["detail"] == "Normal Goal"
    assert payload["statistics"][0]["statistics"][0] == {
        "name": "Ball Possession",
        "value": "58%",
    }
    assert payload["lineups"][0]["formation"] == "4-3-3"
    assert payload["lineups"][0]["starting_xi"][0]["name"] == "A. Keeper"
    assert "cache" not in payload
    assert "quota" not in payload


def test_provider_status_is_admin_only(client, fan):
    original = client.app.state.sports_provider
    client.app.state.sports_provider = MatchdayProvider()
    try:
        forbidden = client.get("/api/v1/admin/provider-status", headers=fan["headers"])
        with client.app.state.session_factory() as db:
            user = db.get(User, fan["user"]["id"])
            user.role = "admin"
            db.commit()
        allowed = client.get("/api/v1/admin/provider-status", headers=fan["headers"])
    finally:
        client.app.state.sports_provider = original

    assert forbidden.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json() == {
        "quota": {
            "daily_limit": 100,
            "daily_remaining": 70,
            "minute_limit": 10,
            "minute_remaining": 8,
            "observed_at": "2026-08-13T20:00:01+00:00",
        },
        "cache": {
            "matchday_entries": 1,
            "fixture_detail_entries": 1,
            "persistent": True,
        },
    }


def test_fixture_detail_not_found_does_not_make_detail_call(client):
    original = client.app.state.sports_provider
    client.app.state.sports_provider = MatchdayProvider()
    try:
        response = client.get("/api/v1/fixtures/999?date=2026-08-13")
    finally:
        client.app.state.sports_provider = original
    assert response.status_code == 404


def test_matchday_rejects_invalid_timezone(client):
    response = client.get(
        "/api/v1/fixtures/matchday?date=2026-08-13&timezone=Not%2FAZone"
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid timezone"


def test_local_matchday_uses_shared_utc_snapshots_and_filters_kickoffs():
    chicago = ZoneInfo("America/Chicago")
    late_fixture = fixture(91, "NS")
    late_fixture = ProviderFixture(
        **{**late_fixture.__dict__, "kickoff": "2026-08-14T03:30:00+00:00"}
    )

    assert local_matchday_utc_dates(date(2026, 8, 13), chicago) == [
        date(2026, 8, 13),
        date(2026, 8, 14),
    ]
    assert fixture_is_on_local_date(late_fixture, date(2026, 8, 13), chicago)
    assert not fixture_is_on_local_date(late_fixture, date(2026, 8, 14), chicago)


def test_matchday_excludes_finished_fixtures_from_adjacent_local_days(client):
    class BoundaryProvider(MatchdayProvider):
        def matchday_snapshot(self, fixture_date):
            previous_local_day = ProviderFixture(
                **{
                    **fixture(100, "FT", 90).__dict__,
                    "kickoff": "2026-08-13T04:59:59+00:00",
                }
            )
            selected_local_day = ProviderFixture(
                **{
                    **fixture(101, "FT", 90).__dict__,
                    "kickoff": "2026-08-13T05:00:00+00:00",
                }
            )
            next_local_day = ProviderFixture(
                **{
                    **fixture(102, "FT", 90).__dict__,
                    "kickoff": "2026-08-14T05:00:00+00:00",
                }
            )
            return snapshot([previous_local_day, selected_local_day, next_local_day])

    original = client.app.state.sports_provider
    client.app.state.sports_provider = BoundaryProvider()
    try:
        response = client.get(
            "/api/v1/fixtures/matchday?date=2026-08-13&timezone=America%2FChicago&bucket=full_time"
        )
    finally:
        client.app.state.sports_provider = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_items"] == 1
    assert [item["fixture_id"] for item in payload["fixtures"]] == [101]
    assert payload["fixtures"][0]["kickoff"] == "2026-08-13T00:00:00-05:00"
    assert payload["fixtures"][0]["timezone"] == "America/Chicago"


def test_matchday_uses_provider_timezone_for_naive_kickoff(client):
    class NaiveKickoffProvider(MatchdayProvider):
        def matchday_snapshot(self, fixture_date):
            local_fixture = ProviderFixture(
                **{
                    **fixture(103, "1H", 12).__dict__,
                    "kickoff": "2026-08-13T00:30:00",
                    "timezone": "America/New_York",
                }
            )
            return snapshot([local_fixture])

    original = client.app.state.sports_provider
    client.app.state.sports_provider = NaiveKickoffProvider()
    try:
        response = client.get(
            "/api/v1/fixtures/matchday?date=2026-08-12&timezone=America%2FChicago&bucket=live"
        )
    finally:
        client.app.state.sports_provider = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_items"] == 1
    assert payload["fixtures"][0]["kickoff"] == "2026-08-12T23:30:00-05:00"


def test_matchday_provider_failure_is_controlled(client):
    class FailingProvider:
        def search_teams(self, query):
            return []

        def matchday_snapshot(self, fixture_date):
            raise ValueError("quota exhausted")

    original = client.app.state.sports_provider
    client.app.state.sports_provider = FailingProvider()
    try:
        response = client.get("/api/v1/fixtures/matchday?date=2026-08-13")
    finally:
        client.app.state.sports_provider = original

    assert response.status_code == 503
    assert response.json()["detail"] == "Sports provider is temporarily unavailable"
