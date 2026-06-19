from __future__ import annotations

from datetime import datetime, timezone
from math import exp
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.ml.predict import predict_match
from app.models.entities import Team
from app.services.cache import CacheService, worldcup_cache_key
from app.services.tournament_seed import KNOCKOUT_STAGES, WORLD_CUP_2026_GROUPS

SCHEDULE_TTL_SECONDS = 3 * 60 * 60
STANDINGS_TTL_SECONDS = 45 * 60
LIVE_TTL_SECONDS = 3 * 60
MATCH_DETAILS_TTL_SECONDS = 30 * 60
FINISHED_MATCH_DETAILS_TTL_SECONDS = 365 * 24 * 60 * 60
PREDICTION_TTL_SECONDS = 8 * 60 * 60

FINISHED_STATUS_CODES = {"FT", "AET", "PEN"}
LIVE_STATUS_CODES = {"1H", "HT", "2H", "ET", "BT", "P", "SUSP", "INT", "LIVE"}


class APIFootballClient:
    def __init__(self, cache: CacheService) -> None:
        self.cache = cache
        self.settings = get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.api_football_key)

    def get_worldcup_matches(self) -> list[dict[str, Any]]:
        fixtures = self._cached_api(
            worldcup_cache_key("fixtures", self.settings.api_football_league, self.settings.api_football_season),
            "/fixtures",
            {"league": self.settings.api_football_league, "season": self.settings.api_football_season},
            SCHEDULE_TTL_SECONDS,
        )
        standings = self.get_worldcup_standings()
        return [self._normalize_fixture(item, standings) for item in fixtures]

    def get_next_match(self, db: Session) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc)
        candidates = []
        for match in self.get_worldcup_matches():
            kickoff = parse_datetime(match.get("kickoffTimeUtc"))
            if kickoff and kickoff > now and match.get("status") not in FINISHED_STATUS_CODES:
                candidates.append((kickoff, match))
        if not candidates:
            return None
        match = sorted(candidates, key=lambda row: row[0])[0][1]
        match["prediction"] = self.get_prediction(db, int(match["fixtureId"]))
        return match

    def get_live_matches(self) -> list[dict[str, Any]]:
        fixtures = self._cached_api(
            worldcup_cache_key("live"),
            "/fixtures",
            {"live": "all"},
            LIVE_TTL_SECONDS,
        )
        standings = self.get_worldcup_standings()
        return [self._normalize_fixture(item, standings) for item in fixtures]

    def get_match_details(self, fixture_id: int, db: Session) -> dict[str, Any]:
        fixture_rows = self._cached_api(
            worldcup_cache_key("fixture", fixture_id),
            "/fixtures",
            {"id": fixture_id},
            MATCH_DETAILS_TTL_SECONDS,
        )
        fixture = fixture_rows[0] if fixture_rows else {}
        normalized = self._normalize_fixture(fixture, self.get_worldcup_standings()) if fixture else {
            "fixtureId": fixture_id,
            "stage": "Data not available yet",
            "group": None,
            "homeTeam": "Data not available yet",
            "awayTeam": "Data not available yet",
            "homeLogo": None,
            "awayLogo": None,
            "kickoffTimeUtc": None,
            "venue": "Data not available yet",
            "city": None,
            "country": None,
            "status": "Data not available yet",
            "homeScore": None,
            "awayScore": None,
            "winner": None,
            "elapsedMinute": None,
            "dataQuality": self._data_quality(),
        }
        ttl = FINISHED_MATCH_DETAILS_TTL_SECONDS if normalized.get("status") in FINISHED_STATUS_CODES else MATCH_DETAILS_TTL_SECONDS
        events = self._cached_api(worldcup_cache_key("events", fixture_id), "/fixtures/events", {"fixture": fixture_id}, ttl)
        statistics = self._cached_api(
            worldcup_cache_key("statistics", fixture_id),
            "/fixtures/statistics",
            {"fixture": fixture_id},
            ttl,
        )
        lineups = self._cached_api(worldcup_cache_key("lineups", fixture_id), "/fixtures/lineups", {"fixture": fixture_id}, ttl)
        details = {
            **normalized,
            "timeline": [self._normalize_event(item) for item in events],
            "statistics": self._normalize_statistics(statistics),
            "lineups": lineups,
            "standings": self.get_worldcup_standings(),
            "prediction": self.get_prediction(db, fixture_id),
            "unavailableFields": [],
        }
        if not fixture:
            details["unavailableFields"].append("match info")
        if not events:
            details["unavailableFields"].append("timeline events")
        if not statistics:
            details["unavailableFields"].append("match statistics")
        if not lineups:
            details["unavailableFields"].append("lineups")
        return details

    def get_worldcup_standings(self) -> list[dict[str, Any]]:
        response = self._cached_api(
            worldcup_cache_key("standings", self.settings.api_football_league, self.settings.api_football_season),
            "/standings",
            {"league": self.settings.api_football_league, "season": self.settings.api_football_season},
            STANDINGS_TTL_SECONDS,
        )
        standings: list[dict[str, Any]] = []
        for league_item in response:
            for group_rows in league_item.get("league", {}).get("standings", []):
                for row in group_rows:
                    all_stats = row.get("all", {})
                    goals = all_stats.get("goals", {})
                    team = row.get("team", {})
                    standings.append(
                        {
                            "group": row.get("group") or "Data not available yet",
                            "team": team.get("name") or "Data not available yet",
                            "teamLogo": team.get("logo"),
                            "played": all_stats.get("played", 0) or 0,
                            "won": all_stats.get("win", 0) or 0,
                            "drawn": all_stats.get("draw", 0) or 0,
                            "lost": all_stats.get("lose", 0) or 0,
                            "goalsFor": goals.get("for", 0) or 0,
                            "goalsAgainst": goals.get("against", 0) or 0,
                            "goalDifference": row.get("goalsDiff", 0) or 0,
                            "points": row.get("points", 0) or 0,
                            "rank": row.get("rank", 0) or 0,
                            "form": row.get("form") or "-",
                        }
                    )
        return standings

    def get_prediction(self, db: Session, fixture_id: int) -> dict[str, Any]:
        cached = self.cache.get_json(worldcup_cache_key("prediction", fixture_id))
        if cached is not None:
            return cached
        api_rows = self._api_get("/predictions", {"fixture": fixture_id})
        api_prediction = self._normalize_api_prediction(api_rows, fixture_id)
        if api_prediction:
            self.cache.set_json(worldcup_cache_key("prediction", fixture_id), api_prediction, PREDICTION_TTL_SECONDS)
            return api_prediction
        fallback = self._internal_prediction(db, fixture_id)
        self.cache.set_json(worldcup_cache_key("prediction", fixture_id), fallback, PREDICTION_TTL_SECONDS)
        return fallback

    def _cached_api(self, key: str, path: str, params: dict[str, Any], ttl_seconds: int) -> list[dict[str, Any]]:
        return self.cache.get_or_set(key, lambda: self._api_get(path, params), ttl_seconds=ttl_seconds)

    def _api_get(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.configured:
            return []
        headers = {"x-apisports-key": self.settings.api_football_key or ""}
        try:
            with httpx.Client(
                base_url=self.settings.api_football_base_url,
                headers=headers,
                timeout=self.settings.sports_api_timeout_seconds,
            ) as client:
                response = client.get(path, params=params)
                response.raise_for_status()
        except httpx.HTTPError:
            return []
        payload = response.json()
        return payload.get("response", []) if isinstance(payload, dict) else []

    def _normalize_fixture(self, item: dict[str, Any], standings: list[dict[str, Any]]) -> dict[str, Any]:
        fixture = item.get("fixture", {})
        league = item.get("league", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        venue = fixture.get("venue", {})
        status = fixture.get("status", {})
        home = teams.get("home", {})
        away = teams.get("away", {})
        group = group_from_round_or_standings(league.get("round"), home.get("name"), away.get("name"), standings)
        winner = winner_name(home, away)
        return {
            "fixtureId": fixture.get("id"),
            "id": fixture.get("id"),
            "stage": stage_from_round(league.get("round")),
            "group": group,
            "homeTeam": home.get("name") or "Data not available yet",
            "awayTeam": away.get("name") or "Data not available yet",
            "homeLogo": home.get("logo"),
            "awayLogo": away.get("logo"),
            "kickoffTimeUtc": fixture.get("date"),
            "venue": venue.get("name") or "Data not available yet",
            "city": venue.get("city"),
            "country": league.get("country"),
            "status": status.get("short") or status.get("long") or "Data not available yet",
            "statusLong": status.get("long"),
            "homeScore": goals.get("home"),
            "awayScore": goals.get("away"),
            "winner": winner,
            "elapsedMinute": status.get("elapsed"),
            "resultText": result_text(home.get("name"), away.get("name"), goals.get("home"), goals.get("away"), winner),
            "dataQuality": "Live sports API data." if self.configured else self._data_quality(),
        }

    def _normalize_event(self, item: dict[str, Any]) -> dict[str, Any]:
        time = item.get("time", {})
        team = item.get("team", {})
        player = item.get("player", {})
        assist = item.get("assist", {})
        return {
            "minute": time.get("elapsed"),
            "extraMinute": time.get("extra"),
            "type": item.get("type") or "Data not available yet",
            "team": team.get("name"),
            "player": player.get("name"),
            "assist": assist.get("name"),
            "detail": item.get("detail"),
            "cardType": item.get("detail") if item.get("type") == "Card" else None,
        }

    def _normalize_statistics(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = []
        for row in rows:
            normalized.append(
                {
                    "team": row.get("team", {}).get("name"),
                    "teamLogo": row.get("team", {}).get("logo"),
                    "statistics": row.get("statistics", []),
                }
            )
        return normalized

    def _normalize_api_prediction(self, rows: list[dict[str, Any]], fixture_id: int) -> dict[str, Any] | None:
        if not rows:
            return None
        row = rows[0]
        predictions = row.get("predictions", {})
        percent = predictions.get("percent", {})
        teams = row.get("teams", {})
        home_name = teams.get("home", {}).get("name", "Home")
        away_name = teams.get("away", {}).get("name", "Away")
        home = percent_to_number(percent.get("home"))
        draw = percent_to_number(percent.get("draw"))
        away = percent_to_number(percent.get("away"))
        if home is None or draw is None or away is None:
            return None
        return {
            "fixtureId": fixture_id,
            "homeWinProbability": home,
            "drawProbability": draw,
            "awayWinProbability": away,
            "predictedScore": self._prediction_score_text(home_name, away_name, row),
            "confidence": confidence_label(home, draw, away),
            "explanation": predictions.get("advice") or "API-Football prediction data.",
            "source": "api-football",
        }

    def _internal_prediction(self, db: Session, fixture_id: int) -> dict[str, Any]:
        detail_rows = self._cached_api(worldcup_cache_key("fixture", fixture_id), "/fixtures", {"id": fixture_id}, MATCH_DETAILS_TTL_SECONDS)
        fixture = detail_rows[0] if detail_rows else {}
        teams = fixture.get("teams", {}) if fixture else {}
        home_name = teams.get("home", {}).get("name", "Home")
        away_name = teams.get("away", {}).get("name", "Away")
        home_team = find_team(db, home_name)
        away_team = find_team(db, away_name)
        if home_team and away_team:
            kickoff = parse_datetime(fixture.get("fixture", {}).get("date")) or datetime.now(timezone.utc)
            local = predict_match(db, home_team, away_team, "neutral", kickoff.date())
            score = local.most_likely_scorelines[0].score if local.most_likely_scorelines else "1-1"
            return {
                "fixtureId": fixture_id,
                "homeWinProbability": round(local.team_a_win_probability * 100, 1),
                "drawProbability": round(local.draw_probability * 100, 1),
                "awayWinProbability": round(local.team_b_win_probability * 100, 1),
                "predictedScore": f"{home_name} {score} {away_name}",
                "confidence": local.confidence.title(),
                "explanation": local.explanation,
                "source": "internal-model",
            }
        standings = self.get_worldcup_standings()
        home_row = standing_for_team(standings, home_name)
        away_row = standing_for_team(standings, away_name)
        home, draw, away, explanation = simple_prediction(home_row, away_row, home_name, away_name)
        return {
            "fixtureId": fixture_id,
            "homeWinProbability": home,
            "drawProbability": draw,
            "awayWinProbability": away,
            "predictedScore": f"{home_name} {predicted_score(home, away)} {away_name}",
            "confidence": confidence_label(home, draw, away),
            "explanation": explanation,
            "source": "internal-standings",
        }

    def _prediction_score_text(self, home_name: str, away_name: str, row: dict[str, Any]) -> str:
        goals = row.get("predictions", {}).get("goals", {})
        home_goals = goals.get("home")
        away_goals = goals.get("away")
        if isinstance(home_goals, str) and isinstance(away_goals, str) and home_goals.isdigit() and away_goals.isdigit():
            return f"{home_name} {home_goals}-{away_goals} {away_name}"
        return f"{home_name} vs {away_name}"

    def _data_quality(self) -> str:
        return "Data not available yet. Set API_FOOTBALL_KEY on the backend to load API-Football data."


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def stage_from_round(round_name: str | None) -> str:
    if not round_name:
        return "Data not available yet"
    lower = round_name.lower()
    if "group" in lower:
        return "Group Stage"
    for stage in KNOCKOUT_STAGES:
        if stage.lower() in lower:
            return stage
    if "32" in lower:
        return "Round of 32"
    if "16" in lower:
        return "Round of 16"
    if "quarter" in lower:
        return "Quarter-finals"
    if "semi" in lower:
        return "Semi-finals"
    if "third" in lower:
        return "Third-place match"
    if "final" in lower:
        return "Final"
    return round_name


def group_from_round_or_standings(
    round_name: str | None,
    home_name: str | None,
    away_name: str | None,
    standings: list[dict[str, Any]],
) -> str | None:
    if round_name:
        for part in round_name.replace("-", " ").split():
            if len(part) == 1 and part.isalpha():
                return f"Group {part.upper()}"
    for team_name in (home_name, away_name):
        row = standing_for_team(standings, team_name or "")
        if row and row.get("group"):
            return row["group"]
    for group, teams in WORLD_CUP_2026_GROUPS.items():
        if home_name in teams or away_name in teams:
            return group
    return None


def winner_name(home: dict[str, Any], away: dict[str, Any]) -> str | None:
    if home.get("winner") is True:
        return home.get("name")
    if away.get("winner") is True:
        return away.get("name")
    return None


def result_text(home: str | None, away: str | None, home_score: int | None, away_score: int | None, winner: str | None) -> str | None:
    if home_score is None or away_score is None or not home or not away:
        return None
    if home_score == away_score:
        return f"{home} drew {home_score}-{away_score} with {away}"
    if winner:
        loser = away if winner == home else home
        return f"{winner} won {max(home_score, away_score)}-{min(home_score, away_score)} against {loser}"
    leading = home if home_score > away_score else away
    trailing = away if home_score > away_score else home
    return f"{leading} won {max(home_score, away_score)}-{min(home_score, away_score)} against {trailing}"


def percent_to_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.replace("%", "").strip()
    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None


def confidence_label(home: float, draw: float, away: float) -> str:
    spread = max(home, draw, away) - min(home, draw, away)
    if spread >= 38:
        return "High"
    if spread >= 18:
        return "Medium"
    return "Low"


def find_team(db: Session, name: str) -> Team | None:
    if not name or name in {"Home", "Away"}:
        return None
    return db.scalar(select(Team).where(Team.name.ilike(name)))


def standing_for_team(standings: list[dict[str, Any]], team_name: str) -> dict[str, Any] | None:
    normalized = team_name.lower()
    for row in standings:
        if row.get("team", "").lower() == normalized:
            return row
    return None


def simple_prediction(
    home: dict[str, Any] | None,
    away: dict[str, Any] | None,
    home_name: str,
    away_name: str,
) -> tuple[float, float, float, str]:
    if not home or not away:
        return 34.0, 32.0, 34.0, "API prediction and standings data are not available yet, so this is a neutral internal estimate."
    home_strength = team_strength(home)
    away_strength = team_strength(away)
    diff = home_strength - away_strength
    home_raw = 1 / (1 + exp(-diff / 8))
    draw = max(18.0, min(32.0, 28.0 - abs(diff) * 0.7))
    remaining = 100.0 - draw
    home_prob = remaining * home_raw
    away_prob = remaining - home_prob
    leader = home_name if home_prob >= away_prob else away_name
    explanation = f"{leader} rates higher on group points, goal difference, goals scored, and recent form."
    return round(home_prob, 1), round(draw, 1), round(away_prob, 1), explanation


def team_strength(row: dict[str, Any]) -> float:
    form_score = sum({"W": 2, "D": 0.5, "L": -1}.get(char, 0) for char in str(row.get("form", ""))[-5:])
    return (
        float(row.get("points", 0))
        + float(row.get("goalDifference", 0)) * 0.8
        + float(row.get("goalsFor", 0)) * 0.35
        - float(row.get("goalsAgainst", 0)) * 0.25
        + form_score
    )


def predicted_score(home_probability: float, away_probability: float) -> str:
    if abs(home_probability - away_probability) < 7:
        return "1-1"
    if home_probability > away_probability:
        return "2-1" if home_probability < 58 else "2-0"
    return "1-2" if away_probability < 58 else "0-2"
