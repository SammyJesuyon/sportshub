from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timezone
import json
from pathlib import Path
from threading import RLock
from time import time
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


@dataclass(frozen=True)
class ProviderFixtureEvent:
    elapsed: Optional[int]
    extra: Optional[int]
    team_name: str
    player_name: Optional[str]
    assist_name: Optional[str]
    event_type: str
    detail: str


@dataclass(frozen=True)
class ProviderFixtureStatistic:
    name: str
    value: Optional[str]


@dataclass(frozen=True)
class ProviderTeamStatistics:
    provider_id: Optional[int]
    team_name: str
    logo_url: Optional[str]
    statistics: list[ProviderFixtureStatistic]


@dataclass(frozen=True)
class ProviderLineupPlayer:
    provider_id: Optional[int]
    name: str
    number: Optional[int]
    position: Optional[str]
    grid: Optional[str]


@dataclass(frozen=True)
class ProviderTeamLineup:
    provider_id: Optional[int]
    team_name: str
    logo_url: Optional[str]
    formation: Optional[str]
    coach_name: Optional[str]
    starting_xi: list[ProviderLineupPlayer]
    substitutes: list[ProviderLineupPlayer]


@dataclass(frozen=True)
class ProviderFixtureDetail:
    fixture: ProviderFixture
    referee: Optional[str]
    venue_name: Optional[str]
    venue_city: Optional[str]
    halftime_home: Optional[int]
    halftime_away: Optional[int]
    fulltime_home: Optional[int]
    fulltime_away: Optional[int]
    extratime_home: Optional[int]
    extratime_away: Optional[int]
    penalty_home: Optional[int]
    penalty_away: Optional[int]
    events: list[ProviderFixtureEvent]
    statistics: list[ProviderTeamStatistics]
    lineups: list[ProviderTeamLineup]


@dataclass(frozen=True)
class ProviderQuota:
    daily_limit: Optional[int] = None
    daily_remaining: Optional[int] = None
    minute_limit: Optional[int] = None
    minute_remaining: Optional[int] = None
    observed_at: Optional[str] = None


@dataclass(frozen=True)
class ProviderMatchdaySnapshot:
    fixtures: list[ProviderFixture]
    cache_hit: bool
    cache_age_seconds: int
    cache_ttl_seconds: int
    quota: ProviderQuota


@dataclass(frozen=True)
class ProviderFixtureDetailSnapshot:
    detail: ProviderFixtureDetail
    cache_hit: bool
    cache_age_seconds: int
    cache_ttl_seconds: int
    quota: ProviderQuota


@dataclass(frozen=True)
class ProviderOperationalStatus:
    quota: ProviderQuota
    matchday_cache_entries: int
    fixture_detail_cache_entries: int
    persistent_cache_enabled: bool


@dataclass
class _CacheEntry:
    stored_at: float
    ttl_seconds: int
    value: Any


class SportsProvider(Protocol):
    def search_teams(self, query: str) -> list[ProviderTeam]: ...

    def matchday_snapshot(self, fixture_date: date) -> ProviderMatchdaySnapshot: ...

    def fixture_detail(
        self, fixture: ProviderFixture
    ) -> ProviderFixtureDetailSnapshot: ...

    def operational_status(self) -> ProviderOperationalStatus: ...


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

    def matchday_snapshot(self, fixture_date: date) -> ProviderMatchdaySnapshot:
        return ProviderMatchdaySnapshot([], True, 0, 3600, ProviderQuota())

    def fixture_detail(self, fixture: ProviderFixture) -> ProviderFixtureDetailSnapshot:
        detail = ProviderFixtureDetail(
            fixture=fixture,
            referee=None,
            venue_name=None,
            venue_city=None,
            halftime_home=None,
            halftime_away=None,
            fulltime_home=None,
            fulltime_away=None,
            extratime_home=None,
            extratime_away=None,
            penalty_home=None,
            penalty_away=None,
            events=[],
            statistics=[],
            lineups=[],
        )
        return ProviderFixtureDetailSnapshot(detail, True, 0, 3600, ProviderQuota())

    def operational_status(self) -> ProviderOperationalStatus:
        return ProviderOperationalStatus(
            quota=ProviderQuota(),
            matchday_cache_entries=0,
            fixture_detail_cache_entries=0,
            persistent_cache_enabled=False,
        )


class ApiSportsAdapter:
    """Quota-aware API-Sports boundary for football teams and fixtures."""

    def __init__(self, api_key: str, base_url: str, cache_path: Optional[str] = None):
        if not api_key:
            raise ValueError("API_SPORTS_KEY is required when SPORTS_PROVIDER=api-sports")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.cache_path = Path(cache_path) if cache_path else None
        self._matchday_cache: dict[date, _CacheEntry] = {}
        self._detail_cache: dict[int, _CacheEntry] = {}
        self._cache_lock = RLock()
        self._quota = ProviderQuota()
        self._restore_cache()

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

    def matchday_snapshot(self, fixture_date: date) -> ProviderMatchdaySnapshot:
        with self._cache_lock:
            cached = self._matchday_cache.get(fixture_date)
            if cached and self._is_fresh(cached):
                return self._matchday_result(cached, True)

            payload = self._get(
                "fixtures", {"date": fixture_date.isoformat(), "timezone": "UTC"}
            )
            fixtures = [
                fixture
                for item in payload.get("response", [])
                if (fixture := self._normalize_fixture(item)) is not None
            ]
            entry = _CacheEntry(
                stored_at=time(),
                ttl_seconds=self._matchday_ttl(fixture_date, fixtures),
                value=fixtures,
            )
            self._matchday_cache = {fixture_date: entry}
            self._persist_cache()
            return self._matchday_result(entry, False)

    def fixture_detail(
        self, fixture: ProviderFixture
    ) -> ProviderFixtureDetailSnapshot:
        with self._cache_lock:
            cached = self._detail_cache.get(fixture.fixture_id)
            if cached and self._is_fresh(cached):
                return self._detail_result(cached, True)

            payload = self._get(
                "fixtures", {"id": fixture.fixture_id, "timezone": "UTC"}
            )
            items = payload.get("response", [])
            detail = self._normalize_fixture_detail(items[0], fixture) if items else None
            if detail is None:
                raise ValueError("API-Sports fixture detail was unavailable")
            if not detail.statistics and self._supplementary_detail_allowed():
                statistics_payload = self._get(
                    "fixtures/statistics", {"fixture": fixture.fixture_id}
                )
                detail = replace(
                    detail,
                    statistics=self._normalize_statistics(
                        statistics_payload.get("response", [])
                    ),
                )
            if not detail.lineups and self._supplementary_detail_allowed():
                lineups_payload = self._get(
                    "fixtures/lineups", {"fixture": fixture.fixture_id}
                )
                detail = replace(
                    detail,
                    lineups=self._normalize_lineups(
                        lineups_payload.get("response", [])
                    ),
                )
            entry = _CacheEntry(
                stored_at=time(),
                ttl_seconds=self._detail_ttl(fixture),
                value=detail,
            )
            self._detail_cache[fixture.fixture_id] = entry
            self._persist_cache()
            return self._detail_result(entry, False)

    def operational_status(self) -> ProviderOperationalStatus:
        with self._cache_lock:
            return ProviderOperationalStatus(
                quota=self._quota,
                matchday_cache_entries=len(self._matchday_cache),
                fixture_detail_cache_entries=len(self._detail_cache),
                persistent_cache_enabled=self.cache_path is not None,
            )

    def _get(self, resource: str, params: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{self.base_url}/{resource}",
                params=params,
                headers={"x-apisports-key": self.api_key},
            )
            self._capture_quota(response.headers)
            response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            raise ValueError("API-Sports rejected the request")
        return payload

    def _capture_quota(self, headers: httpx.Headers) -> None:
        self._quota = ProviderQuota(
            daily_limit=self._header_int(headers, "x-ratelimit-requests-limit"),
            daily_remaining=self._header_int(headers, "x-ratelimit-requests-remaining"),
            minute_limit=self._header_int(headers, "x-ratelimit-limit"),
            minute_remaining=self._header_int(headers, "x-ratelimit-remaining"),
            observed_at=datetime.now(timezone.utc).isoformat(),
        )
        self._persist_cache()

    def _matchday_ttl(
        self, fixture_date: date, fixtures: list[ProviderFixture]
    ) -> int:
        today = datetime.now(timezone.utc).date()
        buckets = {fixture_bucket(fixture.status_short) for fixture in fixtures}
        if fixture_date < today:
            base_ttl = 86_400
        elif "live" in buckets or "half_time" in buckets:
            base_ttl = 300
        elif "scheduled" in buckets:
            base_ttl = 1_800
        else:
            base_ttl = 21_600
        return self._quota_adjusted_ttl(base_ttl)

    def _detail_ttl(self, fixture: ProviderFixture) -> int:
        bucket = fixture_bucket(fixture.status_short)
        base_ttl = {
            "live": 300,
            "half_time": 300,
            "full_time": 86_400,
            "scheduled": 1_800,
        }[bucket]
        return self._quota_adjusted_ttl(base_ttl)

    def _quota_adjusted_ttl(self, base_ttl: int) -> int:
        remaining = self._quota.daily_remaining
        if remaining is None:
            return base_ttl
        if remaining <= 10:
            return max(base_ttl, 21_600)
        if remaining <= 25:
            return max(base_ttl, 3_600)
        if remaining <= 50:
            return max(base_ttl, 900)
        return base_ttl

    def _supplementary_detail_allowed(self) -> bool:
        remaining = self._quota.daily_remaining
        return remaining is None or remaining > 10

    @staticmethod
    def _is_fresh(entry: _CacheEntry) -> bool:
        return time() - entry.stored_at < entry.ttl_seconds

    def _matchday_result(
        self, entry: _CacheEntry, cache_hit: bool
    ) -> ProviderMatchdaySnapshot:
        return ProviderMatchdaySnapshot(
            fixtures=list(entry.value),
            cache_hit=cache_hit,
            cache_age_seconds=max(0, int(time() - entry.stored_at)),
            cache_ttl_seconds=entry.ttl_seconds,
            quota=self._quota,
        )

    def _detail_result(
        self, entry: _CacheEntry, cache_hit: bool
    ) -> ProviderFixtureDetailSnapshot:
        return ProviderFixtureDetailSnapshot(
            detail=entry.value,
            cache_hit=cache_hit,
            cache_age_seconds=max(0, int(time() - entry.stored_at)),
            cache_ttl_seconds=entry.ttl_seconds,
            quota=self._quota,
        )

    @staticmethod
    def _header_int(headers: httpx.Headers, name: str) -> Optional[int]:
        raw_value = headers.get(name)
        try:
            return int(raw_value) if raw_value is not None else None
        except ValueError:
            return None

    def _persist_cache(self) -> None:
        if self.cache_path is None:
            return
        payload = {
            "version": 3,
            "quota": asdict(self._quota),
            "matchdays": {
                key.isoformat(): {
                    "stored_at": entry.stored_at,
                    "ttl_seconds": entry.ttl_seconds,
                    "fixtures": [asdict(fixture) for fixture in entry.value],
                }
                for key, entry in self._matchday_cache.items()
            },
            "details": {
                str(key): {
                    "stored_at": entry.stored_at,
                    "ttl_seconds": entry.ttl_seconds,
                    "detail": asdict(entry.value),
                }
                for key, entry in self._detail_cache.items()
            },
        }
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.cache_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload), encoding="utf-8")
        temporary.replace(self.cache_path)

    def _restore_cache(self) -> None:
        if self.cache_path is None or not self.cache_path.exists():
            return
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            self._quota = ProviderQuota(**payload.get("quota", {}))
            for raw_date, cached in payload.get("matchdays", {}).items():
                entry = _CacheEntry(
                    stored_at=float(cached["stored_at"]),
                    ttl_seconds=int(cached["ttl_seconds"]),
                    value=[self._fixture_from_dict(item) for item in cached["fixtures"]],
                )
                if self._is_fresh(entry):
                    self._matchday_cache[date.fromisoformat(raw_date)] = entry
            if payload.get("version") == 3:
                for raw_id, cached in payload.get("details", {}).items():
                    entry = _CacheEntry(
                        stored_at=float(cached["stored_at"]),
                        ttl_seconds=int(cached["ttl_seconds"]),
                        value=self._detail_from_dict(cached["detail"]),
                    )
                    if self._is_fresh(entry):
                        self._detail_cache[int(raw_id)] = entry
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            self._matchday_cache = {}
            self._detail_cache = {}

    @staticmethod
    def _fixture_from_dict(item: dict[str, Any]) -> ProviderFixture:
        return ProviderFixture(
            **{
                **item,
                "home": ProviderFixtureTeam(**item["home"]),
                "away": ProviderFixtureTeam(**item["away"]),
            }
        )

    @classmethod
    def _detail_from_dict(cls, item: dict[str, Any]) -> ProviderFixtureDetail:
        return ProviderFixtureDetail(
            **{
                **item,
                "fixture": cls._fixture_from_dict(item["fixture"]),
                "events": [ProviderFixtureEvent(**event) for event in item["events"]],
                "statistics": [
                    ProviderTeamStatistics(
                        **{
                            **team,
                            "statistics": [
                                ProviderFixtureStatistic(**statistic)
                                for statistic in team["statistics"]
                            ],
                        }
                    )
                    for team in item.get("statistics", [])
                ],
                "lineups": [
                    ProviderTeamLineup(
                        **{
                            **lineup,
                            "starting_xi": [
                                ProviderLineupPlayer(**player)
                                for player in lineup["starting_xi"]
                            ],
                            "substitutes": [
                                ProviderLineupPlayer(**player)
                                for player in lineup["substitutes"]
                            ],
                        }
                    )
                    for lineup in item.get("lineups", [])
                ],
            }
        )

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

    @classmethod
    def _normalize_fixture_detail(
        cls, item: dict[str, Any], fallback: ProviderFixture
    ) -> Optional[ProviderFixtureDetail]:
        fixture = cls._normalize_fixture(item) or fallback
        fixture_data = item.get("fixture", {})
        venue = fixture_data.get("venue", {})
        score = item.get("score", {})
        events = []
        for event in item.get("events", []):
            time = event.get("time", {})
            team = event.get("team", {})
            player = event.get("player", {})
            assist = event.get("assist", {})
            events.append(
                ProviderFixtureEvent(
                    elapsed=time.get("elapsed"),
                    extra=time.get("extra"),
                    team_name=team.get("name") or "Team",
                    player_name=player.get("name"),
                    assist_name=assist.get("name"),
                    event_type=event.get("type") or "Event",
                    detail=event.get("detail") or "Match event",
                )
            )
        statistics = cls._normalize_statistics(item.get("statistics", []))
        lineups = cls._normalize_lineups(item.get("lineups", []))
        return ProviderFixtureDetail(
            fixture=fixture,
            referee=fixture_data.get("referee"),
            venue_name=venue.get("name"),
            venue_city=venue.get("city"),
            halftime_home=(score.get("halftime") or {}).get("home"),
            halftime_away=(score.get("halftime") or {}).get("away"),
            fulltime_home=(score.get("fulltime") or {}).get("home"),
            fulltime_away=(score.get("fulltime") or {}).get("away"),
            extratime_home=(score.get("extratime") or {}).get("home"),
            extratime_away=(score.get("extratime") or {}).get("away"),
            penalty_home=(score.get("penalty") or {}).get("home"),
            penalty_away=(score.get("penalty") or {}).get("away"),
            events=events,
            statistics=statistics,
            lineups=lineups,
        )

    @staticmethod
    def _normalize_statistics(items: list[dict[str, Any]]) -> list[ProviderTeamStatistics]:
        statistics = []
        for team_summary in items:
            team = team_summary.get("team") or {}
            normalized_statistics = []
            for statistic in team_summary.get("statistics", []):
                name = statistic.get("type")
                if not name:
                    continue
                raw_value = statistic.get("value")
                normalized_statistics.append(
                    ProviderFixtureStatistic(
                        name=str(name),
                        value=None if raw_value is None else str(raw_value),
                    )
                )
            statistics.append(
                ProviderTeamStatistics(
                    provider_id=int(team["id"]) if team.get("id") is not None else None,
                    team_name=team.get("name") or "Team",
                    logo_url=team.get("logo"),
                    statistics=normalized_statistics,
                )
            )
        return statistics

    @classmethod
    def _normalize_lineups(cls, items: list[dict[str, Any]]) -> list[ProviderTeamLineup]:
        lineups = []
        for lineup in items:
            team = lineup.get("team") or {}
            coach = lineup.get("coach") or {}
            lineups.append(
                ProviderTeamLineup(
                    provider_id=int(team["id"]) if team.get("id") is not None else None,
                    team_name=team.get("name") or "Team",
                    logo_url=team.get("logo"),
                    formation=lineup.get("formation"),
                    coach_name=coach.get("name"),
                    starting_xi=cls._normalize_lineup_players(lineup.get("startXI", [])),
                    substitutes=cls._normalize_lineup_players(lineup.get("substitutes", [])),
                )
            )
        return lineups

    @staticmethod
    def _normalize_lineup_players(items: list[dict[str, Any]]) -> list[ProviderLineupPlayer]:
        players = []
        for item in items:
            player = item.get("player") or {}
            if not player.get("name"):
                continue
            players.append(
                ProviderLineupPlayer(
                    provider_id=(
                        int(player["id"]) if player.get("id") is not None else None
                    ),
                    name=player["name"],
                    number=player.get("number"),
                    position=player.get("pos"),
                    grid=player.get("grid"),
                )
            )
        return players
