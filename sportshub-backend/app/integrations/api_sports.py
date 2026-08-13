from dataclasses import dataclass
from datetime import date
from threading import Lock
from time import monotonic
from typing import Any, Optional, Protocol

import httpx


@dataclass(frozen=True)
class ProviderTeam:
    provider_id: int
    name: str
    country: Optional[str] = None
    logo_url: Optional[str] = None


@dataclass(frozen=True)
class ProviderFixtureTeam:
    provider_id: int
    name: str
    logo_url: Optional[str]
    goals: Optional[int]


@dataclass(frozen=True)
class ProviderFixture:
    fixture_id: int
    kickoff: str
    timezone: str
    league_id: int
    league_name: str
    league_logo_url: Optional[str]
    status_short: str
    status_long: str
    elapsed: Optional[int]
    home: ProviderFixtureTeam
    away: ProviderFixtureTeam


class SportsProvider(Protocol):
    def search_teams(self, query: str) -> list[ProviderTeam]: ...

    def fixtures_for_date(self, fixture_date: date) -> list[ProviderFixture]: ...


LIVE_FIXTURE_STATUSES = frozenset({"1H", "2H", "ET", "BT", "P", "LIVE"})
HALF_TIME_FIXTURE_STATUSES = frozenset({"HT"})
FULL_TIME_FIXTURE_STATUSES = frozenset({"FT", "AET", "PEN"})


def fixture_bucket(status_short: str) -> str:
    if status_short in HALF_TIME_FIXTURE_STATUSES:
        return "half_time"
    if status_short in FULL_TIME_FIXTURE_STATUSES:
        return "full_time"
    if status_short in LIVE_FIXTURE_STATUSES:
        return "live"
    return "scheduled"


class SampleSportsAdapter:
    """Deterministic local adapter used for coursework, development, and tests."""

    _teams = (
        ProviderTeam(42, "Arsenal", "England", "https://media.api-sports.io/football/teams/42.png"),
        ProviderTeam(49, "Chelsea", "England", "https://media.api-sports.io/football/teams/49.png"),
        ProviderTeam(40, "Liverpool", "England", "https://media.api-sports.io/football/teams/40.png"),
        ProviderTeam(50, "Manchester City", "England", "https://media.api-sports.io/football/teams/50.png"),
        ProviderTeam(529, "Barcelona", "Spain", "https://media.api-sports.io/football/teams/529.png"),
    )

    def search_teams(self, query: str) -> list[ProviderTeam]:
        normalized = query.casefold()
        return [team for team in self._teams if normalized in team.name.casefold()]

    def fixtures_for_date(self, fixture_date: date) -> list[ProviderFixture]:
        return []


class ApiSportsAdapter:
    """API-Sports boundary for football teams and matchday fixtures."""

    def __init__(self, api_key: str, base_url: str):
        if not api_key:
            raise ValueError("API_SPORTS_KEY is required when SPORTS_PROVIDER=api-sports")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._fixture_cache: dict[date, tuple[float, list[ProviderFixture]]] = {}
        self._fixture_cache_lock = Lock()

    def search_teams(self, query: str) -> list[ProviderTeam]:
        payload = self._get("teams", {"search": query})
        results = []
        for item in payload.get("response", []):
            team = item.get("team", {})
            if team.get("id") and team.get("name"):
                results.append(
                    ProviderTeam(
                        provider_id=int(team["id"]),
                        name=team["name"],
                        country=team.get("country"),
                        logo_url=team.get("logo"),
                    )
                )
        return results

    def fixtures_for_date(self, fixture_date: date) -> list[ProviderFixture]:
        with self._fixture_cache_lock:
            cached = self._fixture_cache.get(fixture_date)
            if cached and monotonic() - cached[0] < 30:
                return list(cached[1])

            payload = self._get(
                "fixtures", {"date": fixture_date.isoformat(), "timezone": "UTC"}
            )
            fixtures = [
                fixture
                for item in payload.get("response", [])
                if (fixture := self._normalize_fixture(item)) is not None
            ]
            self._fixture_cache = {fixture_date: (monotonic(), fixtures)}
            return list(fixtures)

    def _get(self, resource: str, params: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{self.base_url}/{resource}",
                params=params,
                headers={"x-apisports-key": self.api_key},
            )
            response.raise_for_status()
        payload = response.json()
        provider_errors = payload.get("errors")
        if provider_errors:
            raise ValueError("API-Sports rejected the request")
        return payload

    @staticmethod
    def _normalize_fixture(item: dict[str, Any]) -> Optional[ProviderFixture]:
        fixture = item.get("fixture", {})
        league = item.get("league", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        home = teams.get("home", {})
        away = teams.get("away", {})
        status = fixture.get("status", {})
        if not all((fixture.get("id"), fixture.get("date"), league.get("id"), home.get("id"), away.get("id"))):
            return None
        return ProviderFixture(
            fixture_id=int(fixture["id"]),
            kickoff=fixture["date"],
            timezone=fixture.get("timezone") or "UTC",
            league_id=int(league["id"]),
            league_name=league.get("name") or "Competition",
            league_logo_url=league.get("logo"),
            status_short=status.get("short") or "NS",
            status_long=status.get("long") or "Not Started",
            elapsed=status.get("elapsed"),
            home=ProviderFixtureTeam(
                provider_id=int(home["id"]),
                name=home.get("name") or "Home",
                logo_url=home.get("logo"),
                goals=goals.get("home"),
            ),
            away=ProviderFixtureTeam(
                provider_id=int(away["id"]),
                name=away.get("name") or "Away",
                logo_url=away.get("logo"),
                goals=goals.get("away"),
            ),
        )
