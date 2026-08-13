from dataclasses import dataclass
from typing import Optional, Protocol

import httpx


@dataclass(frozen=True)
class ProviderTeam:
    provider_id: int
    name: str
    country: Optional[str] = None
    logo_url: Optional[str] = None


class SportsProvider(Protocol):
    def search_teams(self, query: str) -> list[ProviderTeam]: ...


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


class ApiSportsAdapter:
    """API-Sports boundary for football team search."""

    def __init__(self, api_key: str, base_url: str):
        if not api_key:
            raise ValueError("API_SPORTS_KEY is required when SPORTS_PROVIDER=api-sports")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def search_teams(self, query: str) -> list[ProviderTeam]:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{self.base_url}/teams",
                params={"search": query},
                headers={"x-apisports-key": self.api_key},
            )
            response.raise_for_status()
        payload = response.json()
        provider_errors = payload.get("errors")
        if provider_errors:
            raise ValueError("API-Sports rejected the request")
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
