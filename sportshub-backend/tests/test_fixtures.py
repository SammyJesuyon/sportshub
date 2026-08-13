from datetime import date

from app.integrations.api_sports import ProviderFixture, ProviderFixtureTeam


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


def test_matchday_groups_live_half_time_full_time_and_scheduled(client):
    class MatchdayProvider:
        def search_teams(self, query):
            return []

        def fixtures_for_date(self, fixture_date: date):
            assert fixture_date == date(2026, 8, 13)
            return [
                fixture(4, "NS"),
                fixture(3, "FT", 90),
                fixture(2, "HT", 45),
                fixture(1, "2H", 72),
            ]

    original = client.app.state.sports_provider
    client.app.state.sports_provider = MatchdayProvider()
    try:
        response = client.get("/api/v1/fixtures/matchday?date=2026-08-13")
    finally:
        client.app.state.sports_provider = original

    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == "2026-08-13"
    assert [item["bucket"] for item in payload["fixtures"]] == [
        "live",
        "half_time",
        "full_time",
        "scheduled",
    ]


def test_matchday_provider_failure_is_controlled(client):
    class FailingProvider:
        def search_teams(self, query):
            return []

        def fixtures_for_date(self, fixture_date):
            raise ValueError("quota exhausted")

    original = client.app.state.sports_provider
    client.app.state.sports_provider = FailingProvider()
    try:
        response = client.get("/api/v1/fixtures/matchday?date=2026-08-13")
    finally:
        client.app.state.sports_provider = original

    assert response.status_code == 503
    assert response.json()["detail"] == "Sports provider is temporarily unavailable"
