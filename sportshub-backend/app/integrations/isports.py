from datetime import date, datetime, timezone
import json
from pathlib import Path
from threading import RLock
from time import time
from typing import Any, Optional

import httpx

from app.integrations.api_sports import (
    ApiSportsAdapter,
    ProviderFixture,
    ProviderFixtureDetail,
    ProviderFixtureDetailSnapshot,
    ProviderFixtureEvent,
    ProviderFixtureStatistic,
    ProviderFixtureTeam,
    ProviderLineupPlayer,
    ProviderMatchdaySnapshot,
    ProviderQuota,
    ProviderTeam,
    ProviderTeamLineup,
    ProviderTeamStatistics,
    _CacheEntry,
)


ISPORTS_STATUS = {
    0: ("NS", "Not Started"),
    1: ("1H", "First Half"),
    2: ("HT", "Half Time"),
    3: ("2H", "Second Half"),
    4: ("ET", "Extra Time"),
    5: ("P", "Penalty Shootout"),
    -1: ("FT", "Match Finished"),
    -10: ("CANC", "Cancelled"),
    -11: ("TBD", "Time To Be Defined"),
    -12: ("ABD", "Terminated"),
    -13: ("INT", "Interrupted"),
    -14: ("PST", "Postponed"),
}

ISPORTS_EVENT_TYPES = {
    1: ("Goal", "Goal"),
    2: ("Card", "Red Card"),
    3: ("Card", "Yellow Card"),
    7: ("Goal", "Penalty"),
    8: ("Goal", "Own Goal"),
    9: ("Card", "Second Yellow Card"),
    11: ("Substitution", "Substitution"),
    13: ("Goal", "Penalty Missed"),
    14: ("VAR", "VAR Review"),
}

ISPORTS_STAT_NAMES = {
    3: "Shots",
    4: "Shots on Target",
    5: "Fouls",
    6: "Corner Kicks",
    9: "Offsides",
    11: "Yellow Cards",
    13: "Red Cards",
    14: "Possession",
    16: "Saves",
    19: "Successful Tackles",
    20: "Interceptions",
    23: "Assists",
    24: "Successful Crosses",
    34: "Shots off Target",
    35: "Hit the Post",
    37: "Blocked Shots",
    38: "Tackles",
    39: "Dribbles",
    41: "Passes",
    42: "Pass Accuracy",
    43: "Attacks",
    44: "Dangerous Attacks",
    47: "Big Chances",
    48: "Big Chances Missed",
    49: "Shots Inside Box",
    50: "Shots Outside Box",
    51: "Duels Won",
    52: "Expected Goals",
    53: "xG Open Play",
    54: "xG Set Play",
    55: "xG Non-Penalty",
    56: "xG on Target",
    57: "Touches in Opposition Box",
    58: "Accurate Crosses",
    59: "Ground Duels Won",
    60: "Aerial Duels Won",
    61: "Clearances",
}

ISPORTS_POSITION_NAMES = {
    0: "G",
    1: "D",
    2: "M",
    3: "M",
    4: "M",
    5: "F",
}


class ISportsAdapter(ApiSportsAdapter):
    """Quota-conscious iSportsAPI boundary normalized to SportsHub contracts."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        fallback_base_url: Optional[str] = None,
        cache_path: Optional[str] = None,
    ):
        if not api_key:
            raise ValueError("ISPORTS_API_KEY is required when SPORTS_PROVIDER=isports")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.fallback_base_url = (
            fallback_base_url.rstrip("/") if fallback_base_url else None
        )
        self.cache_path = Path(cache_path) if cache_path else None
        self._matchday_cache: dict[date, _CacheEntry] = {}
        self._detail_cache: dict[int, _CacheEntry] = {}
        self._team_search_cache: dict[str, _CacheEntry] = {}
        self._team_cache: dict[int, _CacheEntry] = {}
        self._team_schedule_cache: dict[int, _CacheEntry] = {}
        self._cache_lock = RLock()
        self._quota = ProviderQuota()
        self._restore_cache()

    def search_teams(self, query: str) -> list[ProviderTeam]:
        cache_key = query.strip().casefold()
        with self._cache_lock:
            cached = self._team_search_cache.get(cache_key)
            if cached and self._is_fresh(cached):
                return list(cached.value)

        payload = self._get("sport/football/team/search", {"name": query.strip()})
        teams = [
            team
            for item in self._items(payload.get("data"))
            if (team := self._normalize_isports_team(item)) is not None
        ]
        with self._cache_lock:
            self._team_search_cache[cache_key] = _CacheEntry(time(), 21_600, teams)
            for team in teams:
                self._team_cache[team.provider_id] = _CacheEntry(time(), 86_400, team)
        return teams

    def get_team(self, provider_id: int) -> Optional[ProviderTeam]:
        with self._cache_lock:
            cached = self._team_cache.get(provider_id)
            if cached and self._is_fresh(cached):
                return cached.value

        payload = self._get("sport/football/team", {"teamId": str(provider_id)})
        teams = [
            team
            for item in self._items(payload.get("data"))
            if (team := self._normalize_isports_team(item)) is not None
        ]
        team = next((item for item in teams if item.provider_id == provider_id), None)
        if team is not None:
            with self._cache_lock:
                self._team_cache[provider_id] = _CacheEntry(time(), 86_400, team)
        return team

    def team_schedule(
        self, provider_id: int, league_provider_id: Optional[int] = None
    ) -> list[ProviderFixture]:
        if league_provider_id is None:
            return []

        with self._cache_lock:
            cached = self._team_schedule_cache.get(league_provider_id)
            if cached and self._is_fresh(cached):
                league_fixtures = list(cached.value)
            else:
                payload = self._get(
                    "sport/football/schedule/basic",
                    {"leagueId": str(league_provider_id)},
                )
                league_fixtures = [
                    fixture
                    for item in self._items(payload.get("data"))
                    if (fixture := self._normalize_isports_fixture(item)) is not None
                ]
                self._team_schedule_cache[league_provider_id] = _CacheEntry(
                    time(), 43_200, league_fixtures
                )
                self._persist_cache()

        return [
            fixture
            for fixture in league_fixtures
            if provider_id in {fixture.home.provider_id, fixture.away.provider_id}
        ]

    def matchday_snapshot(self, fixture_date: date) -> ProviderMatchdaySnapshot:
        with self._cache_lock:
            cached = self._matchday_cache.get(fixture_date)
            if cached and self._is_fresh(cached):
                return self._matchday_result(cached, True)

        today = datetime.now(timezone.utc).date()
        if fixture_date == today:
            payload = self._get("sport/football/livescores", {})
        else:
            payload = self._get(
                "sport/football/schedule/basic",
                {"date": fixture_date.isoformat()},
            )
        fixtures = [
            fixture
            for item in self._items(payload.get("data"))
            if (fixture := self._normalize_isports_fixture(item)) is not None
        ]
        entry = _CacheEntry(
            stored_at=time(),
            ttl_seconds=self._matchday_ttl(fixture_date, fixtures),
            value=fixtures,
        )
        with self._cache_lock:
            self._matchday_cache[fixture_date] = entry
            self._persist_cache()
        return self._matchday_result(entry, False)

    def fixture_detail(
        self, fixture: ProviderFixture
    ) -> ProviderFixtureDetailSnapshot:
        with self._cache_lock:
            cached = self._detail_cache.get(fixture.fixture_id)
            if cached and self._is_fresh(cached):
                return self._detail_result(cached, True)

        raw_fixture: dict[str, Any] = {}
        try:
            schedule = self._get(
                "sport/football/schedule/basic",
                {"matchId": str(fixture.fixture_id)},
            )
            raw_fixture = next(
                (
                    item
                    for item in self._items(schedule.get("data"))
                    if self._as_int(item.get("matchId")) == fixture.fixture_id
                ),
                {},
            )
        except ValueError:
            raw_fixture = {}

        normalized_fixture = self._normalize_isports_fixture(raw_fixture) or fixture
        fixture_day = self._fixture_date(normalized_fixture)
        today = datetime.now(timezone.utc).date()
        within_history_window = 0 <= (today - fixture_day).days <= 30

        events: list[ProviderFixtureEvent] = []
        statistics: list[ProviderTeamStatistics] = []
        if within_history_window:
            events_payload = self._optional_get(
                "sport/football/events", {"date": fixture_day.isoformat()}
            )
            events = self._normalize_isports_events(
                events_payload.get("data"), normalized_fixture
            )
            stats_params = (
                {"matchId": str(fixture.fixture_id)}
                if fixture_day == today
                else {"date": fixture_day.isoformat()}
            )
            stats_payload = self._optional_get("sport/football/stats", stats_params)
            statistics = self._normalize_isports_statistics(
                stats_payload.get("data"), normalized_fixture
            )

        lineups: list[ProviderTeamLineup] = []
        if abs((fixture_day - today).days) <= 3:
            lineup_params: dict[str, Any] = {"matchId": str(fixture.fixture_id)}
            if normalized_fixture.status_short == "NS":
                lineup_params["isPreview"] = "true"
            lineup_payload = self._optional_get(
                "sport/football/lineups", lineup_params
            )
            lineups = self._normalize_isports_lineups(
                lineup_payload.get("data"), normalized_fixture
            )

        extra = raw_fixture.get("extraExplain") or {}
        is_finished = normalized_fixture.status_short in {"FT", "AET", "PEN"}
        detail = ProviderFixtureDetail(
            fixture=normalized_fixture,
            referee=None,
            venue_name=raw_fixture.get("location") or None,
            venue_city=None,
            halftime_home=self._as_int(raw_fixture.get("homeHalfScore")),
            halftime_away=self._as_int(raw_fixture.get("awayHalfScore")),
            fulltime_home=normalized_fixture.home.goals if is_finished else None,
            fulltime_away=normalized_fixture.away.goals if is_finished else None,
            extratime_home=self._as_int(extra.get("extraHomeScore")),
            extratime_away=self._as_int(extra.get("extraAwayScore")),
            penalty_home=self._as_int(extra.get("penHomeScore")),
            penalty_away=self._as_int(extra.get("penAwayScore")),
            events=events,
            statistics=statistics,
            lineups=lineups,
        )
        entry = _CacheEntry(time(), self._detail_ttl(normalized_fixture), detail)
        with self._cache_lock:
            self._detail_cache[fixture.fixture_id] = entry
            self._persist_cache()
        return self._detail_result(entry, False)

    def _get(self, resource: str, params: dict[str, Any]) -> dict[str, Any]:
        request_params = {"api_key": self.api_key, **params}
        bases = [self.base_url]
        if self.fallback_base_url and self.fallback_base_url not in bases:
            bases.append(self.fallback_base_url)

        with httpx.Client(timeout=10.0) as client:
            for index, base_url in enumerate(bases):
                try:
                    response = client.get(
                        f"{base_url}/{resource.lstrip('/')}",
                        params=request_params,
                        headers={"Accept": "application/json"},
                    )
                except httpx.HTTPError:
                    if index + 1 < len(bases):
                        continue
                    raise ValueError("iSportsAPI is currently unavailable") from None

                self._capture_quota(response.headers)
                if response.status_code in {502, 503, 504} and index + 1 < len(bases):
                    continue
                if response.status_code >= 400:
                    raise ValueError("iSportsAPI rejected the request")
                try:
                    payload = response.json()
                except (json.JSONDecodeError, TypeError, ValueError):
                    raise ValueError("iSportsAPI returned an invalid response") from None
                try:
                    code = int(payload.get("code", 0))
                except (TypeError, ValueError):
                    code = -1
                if code != 0:
                    raise ValueError("iSportsAPI rejected the request")
                return payload
        raise ValueError("iSportsAPI is currently unavailable")

    def _optional_get(self, resource: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._get(resource, params)
        except ValueError:
            return {"data": []}

    def _matchday_ttl(
        self, fixture_date: date, fixtures: list[ProviderFixture]
    ) -> int:
        today = datetime.now(timezone.utc).date()
        if fixture_date < today:
            return self._quota_adjusted_ttl(86_400)
        if fixture_date > today:
            return self._quota_adjusted_ttl(21_600)
        return super()._matchday_ttl(fixture_date, fixtures)

    @classmethod
    def _normalize_isports_team(cls, item: dict[str, Any]) -> Optional[ProviderTeam]:
        provider_id = cls._as_int(item.get("teamId"))
        name = item.get("name")
        if provider_id is None or not name:
            return None
        founding_date = str(item.get("foundingDate") or "")
        founded = cls._as_int(founding_date[:4]) if len(founding_date) >= 4 else None
        return ProviderTeam(
            provider_id=provider_id,
            name=str(name),
            country=item.get("country") or item.get("area") or None,
            logo_url=item.get("logo") or None,
            code=item.get("shortName") or None,
            founded=founded,
            national=item.get("isNational"),
            venue_name=item.get("venue") or None,
            venue_address=item.get("address") or None,
            venue_city=item.get("area") or None,
            venue_capacity=cls._as_int(item.get("capacity")),
            venue_surface=None,
            venue_image_url=None,
            league_provider_id=cls._as_int(item.get("leagueId")),
        )

    @classmethod
    def _normalize_isports_fixture(
        cls, item: dict[str, Any]
    ) -> Optional[ProviderFixture]:
        fixture_id = cls._as_int(item.get("matchId"))
        match_time = cls._as_int(item.get("matchTime"))
        league_id = cls._as_int(item.get("leagueId"))
        home_id = cls._as_int(item.get("homeId"))
        away_id = cls._as_int(item.get("awayId"))
        if None in (fixture_id, match_time, league_id, home_id, away_id):
            return None
        status_code = cls._as_int(item.get("status")) or 0
        status_short, status_long = ISPORTS_STATUS.get(
            status_code, ("NS", "Not Started")
        )
        extra = item.get("extraExplain") or {}
        elapsed = cls._as_int(extra.get("minute"))
        if elapsed is None:
            elapsed = {2: 45, -1: 90}.get(status_code)
        show_score = status_code not in {0, -11, -14}
        return ProviderFixture(
            fixture_id=fixture_id,
            kickoff=datetime.fromtimestamp(match_time, timezone.utc).isoformat(),
            timezone="UTC",
            league_id=league_id,
            league_name=item.get("leagueName") or item.get("leagueShortName") or "Competition",
            league_logo_url=None,
            status_short=status_short,
            status_long=status_long,
            elapsed=elapsed,
            home=ProviderFixtureTeam(
                provider_id=home_id,
                name=item.get("homeName") or "Home",
                logo_url=None,
                goals=cls._as_int(item.get("homeScore")) if show_score else None,
            ),
            away=ProviderFixtureTeam(
                provider_id=away_id,
                name=item.get("awayName") or "Away",
                logo_url=None,
                goals=cls._as_int(item.get("awayScore")) if show_score else None,
            ),
        )

    @classmethod
    def _normalize_isports_events(
        cls, data: Any, fixture: ProviderFixture
    ) -> list[ProviderFixtureEvent]:
        match = next(
            (
                item
                for item in cls._items(data)
                if cls._as_int(item.get("matchId")) == fixture.fixture_id
            ),
            {},
        )
        normalized = []
        for event in match.get("events") or []:
            type_code = cls._as_int(event.get("type"))
            event_type, detail = ISPORTS_EVENT_TYPES.get(
                type_code, ("Event", "Match Event")
            )
            player_name, assist_name = cls._split_player_and_assist(
                event.get("playerName")
            )
            normalized.append(
                ProviderFixtureEvent(
                    elapsed=cls._as_int(event.get("minute")),
                    extra=cls._as_int(event.get("overtime")),
                    team_name=(
                        fixture.home.name
                        if event.get("homeEvent") is True
                        else fixture.away.name
                    ),
                    player_name=player_name,
                    assist_name=assist_name,
                    event_type=event_type,
                    detail=detail,
                )
            )
        return normalized

    @classmethod
    def _normalize_isports_statistics(
        cls, data: Any, fixture: ProviderFixture
    ) -> list[ProviderTeamStatistics]:
        match = next(
            (
                item
                for item in cls._items(data)
                if cls._as_int(item.get("matchId")) == fixture.fixture_id
            ),
            {},
        )
        home_stats = []
        away_stats = []
        for statistic in match.get("stats") or []:
            type_code = cls._as_int(statistic.get("type"))
            if type_code not in ISPORTS_STAT_NAMES:
                continue
            name = ISPORTS_STAT_NAMES[type_code]
            home_value = statistic.get("home")
            away_value = statistic.get("away")
            if type_code in {14, 42, 46}:
                home_value = cls._percentage(home_value)
                away_value = cls._percentage(away_value)
            home_stats.append(
                ProviderFixtureStatistic(
                    name=name,
                    value=None if home_value is None else str(home_value),
                )
            )
            away_stats.append(
                ProviderFixtureStatistic(
                    name=name,
                    value=None if away_value is None else str(away_value),
                )
            )
        if not home_stats and not away_stats:
            return []
        return [
            ProviderTeamStatistics(
                provider_id=fixture.home.provider_id,
                team_name=fixture.home.name,
                logo_url=fixture.home.logo_url,
                statistics=home_stats,
            ),
            ProviderTeamStatistics(
                provider_id=fixture.away.provider_id,
                team_name=fixture.away.name,
                logo_url=fixture.away.logo_url,
                statistics=away_stats,
            ),
        ]

    @classmethod
    def _normalize_isports_lineups(
        cls, data: Any, fixture: ProviderFixture
    ) -> list[ProviderTeamLineup]:
        match = next(
            (
                item
                for item in cls._items(data)
                if cls._as_int(item.get("matchId")) == fixture.fixture_id
            ),
            {},
        )
        if not match:
            return []
        return [
            ProviderTeamLineup(
                provider_id=fixture.home.provider_id,
                team_name=fixture.home.name,
                logo_url=fixture.home.logo_url,
                formation=cls._formation(match.get("homeFormation")),
                coach_name=None,
                starting_xi=cls._lineup_players(match.get("homeLineup")),
                substitutes=cls._lineup_players(match.get("homeBackup")),
            ),
            ProviderTeamLineup(
                provider_id=fixture.away.provider_id,
                team_name=fixture.away.name,
                logo_url=fixture.away.logo_url,
                formation=cls._formation(match.get("awayFormation")),
                coach_name=None,
                starting_xi=cls._lineup_players(match.get("awayLineup")),
                substitutes=cls._lineup_players(match.get("awayBackup")),
            ),
        ]

    @classmethod
    def _lineup_players(cls, data: Any) -> list[ProviderLineupPlayer]:
        players = []
        for player in cls._items(data):
            name = player.get("name")
            if not name:
                continue
            position = cls._as_int(player.get("position"))
            players.append(
                ProviderLineupPlayer(
                    provider_id=cls._as_int(player.get("playerId")),
                    name=str(name),
                    number=cls._as_int(player.get("number")),
                    position=ISPORTS_POSITION_NAMES.get(position),
                    grid=None if position is None else str(position),
                )
            )
        return players

    @staticmethod
    def _items(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            return [data]
        return []

    @staticmethod
    def _as_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _fixture_date(fixture: ProviderFixture) -> date:
        return datetime.fromisoformat(fixture.kickoff.replace("Z", "+00:00")).date()

    @staticmethod
    def _formation(value: Any) -> Optional[str]:
        raw = str(value or "").strip()
        if not raw:
            return None
        return "-".join(raw) if raw.isdigit() else raw

    @staticmethod
    def _percentage(value: Any) -> Any:
        if value is None:
            return None
        raw = str(value)
        return raw if raw.endswith("%") else f"{raw}%"

    @staticmethod
    def _split_player_and_assist(value: Any) -> tuple[Optional[str], Optional[str]]:
        raw = str(value or "").strip()
        marker = " (Assist:"
        if marker not in raw or not raw.endswith(")"):
            return (raw or None, None)
        player, assist = raw.split(marker, 1)
        return player.strip() or None, assist[:-1].strip() or None
