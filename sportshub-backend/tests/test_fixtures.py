from datetime import date

from app.integrations.api_sports import (
    ProviderFixture,
    ProviderFixtureDetail,
    ProviderFixtureDetailSnapshot,
    ProviderFixtureEvent,
    ProviderFixtureTeam,
    ProviderMatchdaySnapshot,
    ProviderQuota,
)


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
        assert fixture_date == date(2026, 8, 13)
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
        )
        return ProviderFixtureDetailSnapshot(
            detail=detail,
            cache_hit=False,
            cache_age_seconds=0,
            cache_ttl_seconds=300,
            quota=ProviderQuota(100, 70, 10, 8, "2026-08-13T20:00:01+00:00"),
        )


def test_matchday_paginates_cached_snapshot_and_exposes_quota(client):
    original = client.app.state.sports_provider
    client.app.state.sports_provider = MatchdayProvider()
    try:
        response = client.get(
            "/api/v1/fixtures/matchday?date=2026-08-13&page=1&page_size=2"
        )
        live = client.get(
            "/api/v1/fixtures/matchday?date=2026-08-13&bucket=live&page=1&page_size=12"
        )
    finally:
        client.app.state.sports_provider = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_items"] == 4
    assert payload["total_pages"] == 2
    assert len(payload["fixtures"]) == 2
    assert payload["counts"] == {
        "live": 1,
        "half_time": 1,
        "full_time": 1,
        "scheduled": 1,
    }
    assert payload["cache"] == {"hit": True, "age_seconds": 12, "ttl_seconds": 300}
    assert payload["quota"]["daily_remaining"] == 71
    assert [item["bucket"] for item in live.json()["fixtures"]] == ["live"]


def test_fixture_detail_returns_events_and_cache_metadata(client):
    original = client.app.state.sports_provider
    client.app.state.sports_provider = MatchdayProvider()
    try:
        response = client.get("/api/v1/fixtures/1?date=2026-08-13")
    finally:
        client.app.state.sports_provider = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["fixture"]["fixture_id"] == 1
    assert payload["venue_name"] == "Emirates Stadium"
    assert payload["events"][0]["detail"] == "Normal Goal"
    assert payload["quota"]["daily_remaining"] == 70


def test_fixture_detail_not_found_does_not_make_detail_call(client):
    original = client.app.state.sports_provider
    client.app.state.sports_provider = MatchdayProvider()
    try:
        response = client.get("/api/v1/fixtures/999?date=2026-08-13")
    finally:
        client.app.state.sports_provider = original
    assert response.status_code == 404


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
