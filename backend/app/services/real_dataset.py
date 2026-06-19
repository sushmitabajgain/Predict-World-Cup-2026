import csv
import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Match, Team, TeamRating


CONFEDERATION_BY_TEAM = {
    "Argentina": "CONMEBOL",
    "Brazil": "CONMEBOL",
    "Canada": "CONCACAF",
    "England": "UEFA",
    "France": "UEFA",
    "Germany": "UEFA",
    "Japan": "AFC",
    "Mexico": "CONCACAF",
    "Morocco": "CAF",
    "Netherlands": "UEFA",
    "Portugal": "UEFA",
    "Scotland": "UEFA",
    "Spain": "UEFA",
    "United States": "CONCACAF",
}


@dataclass(frozen=True)
class ResultRow:
    match_date: date
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    tournament: str
    city: str
    country: str
    neutral: bool


def load_result_rows(path: Path) -> list[ResultRow]:
    rows: list[ResultRow] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                rows.append(
                    ResultRow(
                        match_date=date.fromisoformat(row["date"]),
                        home_team=row["home_team"].strip(),
                        away_team=row["away_team"].strip(),
                        home_score=int(row["home_score"]),
                        away_score=int(row["away_score"]),
                        tournament=row["tournament"].strip(),
                        city=row["city"].strip(),
                        country=row["country"].strip(),
                        neutral=row["neutral"].strip().upper() == "TRUE",
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
    return rows


def make_fifa_codes(team_names: list[str], reserved_codes: set[str] | None = None) -> dict[str, str]:
    used: set[str] = set(reserved_codes or set())
    codes: dict[str, str] = {}
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for name in sorted(team_names):
        letters = re.sub(r"[^A-Za-z]", "", name).upper()
        initials = "".join(part[0] for part in re.findall(r"[A-Za-z]+", name)).upper()
        base = (initials + letters + "XXX")[:3]
        candidates = [base]
        candidates.extend(f"{base[:2]}{suffix}" for suffix in alphabet)
        candidates.extend(f"{base[:1]}{a}{b}" for a in alphabet for b in alphabet)
        for candidate in candidates:
            if candidate not in used:
                used.add(candidate)
                codes[name] = candidate
                break
    return codes


def seed_real_dataset(db: Session, dataset_path: Path) -> int:
    rows = load_result_rows(dataset_path)
    if not rows:
        return 0

    team_names = sorted({row.home_team for row in rows} | {row.away_team for row in rows})
    teams_by_name = {team.name: team for team in db.scalars(select(Team)).all()}
    reserved_codes = {team.fifa_code for team in teams_by_name.values()}
    codes = make_fifa_codes(team_names, reserved_codes)

    for name in team_names:
        if name in teams_by_name:
            continue
        team = Team(
            name=name,
            fifa_code=codes[name],
            confederation=CONFEDERATION_BY_TEAM.get(name, "UNKNOWN"),
        )
        db.add(team)
        db.flush()
        teams_by_name[name] = team

    existing_matches = {
        (match.match_date, match.team_a_id, match.team_b_id, match.competition)
        for match in db.scalars(select(Match)).all()
    }
    inserted = 0
    ratings = {name: 1500.0 for name in team_names}

    for row in sorted(rows, key=lambda item: item.match_date):
        home = teams_by_name[row.home_team]
        away = teams_by_name[row.away_team]
        signature = (row.match_date, home.id, away.id, row.tournament)
        if signature not in existing_matches:
            db.add(
                Match(
                    match_date=row.match_date,
                    team_a_id=home.id,
                    team_b_id=away.id,
                    score_a=row.home_score,
                    score_b=row.away_score,
                    competition=row.tournament,
                    venue=f"{row.city}, {row.country}".strip(", "),
                    venue_type="neutral" if row.neutral else "home",
                    is_neutral=row.neutral,
                )
            )
            existing_matches.add(signature)
            inserted += 1

        update_elo(ratings, row)

    latest_date = max(row.match_date for row in rows)
    ranked = sorted(ratings.items(), key=lambda item: item[1], reverse=True)
    ranks = {name: rank for rank, (name, _) in enumerate(ranked, start=1)}
    for name, elo in ranked:
        team = teams_by_name[name]
        rating = db.scalar(
            select(TeamRating).where(
                TeamRating.team_id == team.id,
                TeamRating.rating_date == latest_date,
            )
        )
        if not rating:
            rating = TeamRating(team_id=team.id, rating_date=latest_date, elo_rating=elo, fifa_rank=ranks[name], fifa_points=elo)
            db.add(rating)
        rating.elo_rating = round(elo, 2)
        rating.fifa_rank = ranks[name]
        rating.fifa_points = round(elo, 2)

    db.commit()
    return inserted


def update_elo(ratings: dict[str, float], row: ResultRow) -> None:
    home_advantage = 0 if row.neutral else 60
    rating_home = ratings[row.home_team] + home_advantage
    rating_away = ratings[row.away_team]
    expected_home = 1 / (1 + 10 ** ((rating_away - rating_home) / 400))
    expected_away = 1 - expected_home

    if row.home_score > row.away_score:
        actual_home, actual_away = 1.0, 0.0
    elif row.home_score == row.away_score:
        actual_home, actual_away = 0.5, 0.5
    else:
        actual_home, actual_away = 0.0, 1.0

    goal_diff = abs(row.home_score - row.away_score)
    margin_multiplier = 1.0 if goal_diff <= 1 else 1.0 + math.log(goal_diff)
    k_factor = 24 * margin_multiplier
    ratings[row.home_team] += k_factor * (actual_home - expected_home)
    ratings[row.away_team] += k_factor * (actual_away - expected_away)
