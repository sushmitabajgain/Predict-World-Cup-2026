from dataclasses import dataclass
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.entities import Match, Team, TeamRating


@dataclass(frozen=True)
class TeamProfile:
    team: Team
    rating: TeamRating
    recent_points_per_match: float
    recent_goal_difference: float
    recent_goals_scored: float
    recent_goals_conceded: float


FEATURE_COLUMNS = [
    "elo_diff",
    "fifa_rank_diff",
    "fifa_points_diff",
    "recent_form_diff",
    "recent_goal_difference_diff",
    "goals_scored_recent_diff",
    "goals_conceded_recent_diff",
    "venue_home",
    "venue_away",
    "venue_neutral",
    "rest_days_diff",
]


def latest_rating(db: Session, team_id: int, as_of: date | None = None) -> TeamRating:
    stmt = select(TeamRating).where(TeamRating.team_id == team_id)
    if as_of:
        stmt = stmt.where(TeamRating.rating_date <= as_of)
    stmt = stmt.order_by(TeamRating.rating_date.desc())
    rating = db.scalar(stmt)
    if not rating and as_of:
        rating = db.scalar(
            select(TeamRating)
            .where(TeamRating.team_id == team_id)
            .order_by(TeamRating.rating_date.desc())
        )
    if not rating:
        raise ValueError(f"No rating found for team id {team_id}")
    return rating


def recent_matches(db: Session, team_id: int, as_of: date, limit: int = 5) -> list[Match]:
    stmt = (
        select(Match)
        .where(
            Match.match_date < as_of,
            or_(Match.team_a_id == team_id, Match.team_b_id == team_id),
        )
        .order_by(Match.match_date.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def team_profile(db: Session, team: Team, as_of: date) -> TeamProfile:
    matches = recent_matches(db, team.id, as_of)
    points = goals_for = goals_against = 0

    for match in matches:
        is_team_a = match.team_a_id == team.id
        gf = match.score_a if is_team_a else match.score_b
        ga = match.score_b if is_team_a else match.score_a
        goals_for += gf
        goals_against += ga
        if gf > ga:
            points += 3
        elif gf == ga:
            points += 1

    match_count = max(len(matches), 1)
    return TeamProfile(
        team=team,
        rating=latest_rating(db, team.id, as_of),
        recent_points_per_match=points / match_count,
        recent_goal_difference=(goals_for - goals_against) / match_count,
        recent_goals_scored=goals_for / match_count,
        recent_goals_conceded=goals_against / match_count,
    )


def build_match_features(db: Session, team_a: Team, team_b: Team, venue_type: str, match_date: date) -> dict[str, float]:
    profile_a = team_profile(db, team_a, match_date)
    profile_b = team_profile(db, team_b, match_date)

    features = {
        "elo_diff": profile_a.rating.elo_rating - profile_b.rating.elo_rating,
        "fifa_rank_diff": float(profile_b.rating.fifa_rank - profile_a.rating.fifa_rank),
        "fifa_points_diff": profile_a.rating.fifa_points - profile_b.rating.fifa_points,
        "recent_form_diff": profile_a.recent_points_per_match - profile_b.recent_points_per_match,
        "recent_goal_difference_diff": profile_a.recent_goal_difference - profile_b.recent_goal_difference,
        "goals_scored_recent_diff": profile_a.recent_goals_scored - profile_b.recent_goals_scored,
        "goals_conceded_recent_diff": profile_b.recent_goals_conceded - profile_a.recent_goals_conceded,
        "venue_home": 1.0 if venue_type == "home" else 0.0,
        "venue_away": 1.0 if venue_type == "away" else 0.0,
        "venue_neutral": 1.0 if venue_type == "neutral" else 0.0,
        "rest_days_diff": 0.0,
    }
    return {column: float(features[column]) for column in FEATURE_COLUMNS}


def build_training_frame(db: Session) -> tuple[list[dict[str, float]], list[int]]:
    rows: list[dict[str, float]] = []
    labels: list[int] = []
    settings = get_settings()
    matches = list(
        db.scalars(
            select(Match)
            .order_by(Match.match_date.desc())
            .limit(settings.training_match_limit)
        ).all()
    )
    matches.reverse()
    teams = {team.id: team for team in db.scalars(select(Team)).all()}

    for match in matches:
        team_a = teams.get(match.team_a_id)
        team_b = teams.get(match.team_b_id)
        if not team_a or not team_b:
            continue
        rows.append(build_match_features(db, team_a, team_b, match.venue_type, match.match_date))
        if match.score_a > match.score_b:
            labels.append(0)
        elif match.score_a == match.score_b:
            labels.append(1)
        else:
            labels.append(2)
    return rows, labels
