from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.ml.predict import predict_match
from app.models.entities import MatchEvent, MatchPrediction, MatchStatsSnapshot, Team, Tournament, TournamentMatch
from app.schemas.match_center import (
    MatchDetailRead,
    MatchEventRead,
    MatchPredictionRead,
    MatchTeamRead,
    StandingRead,
    TournamentMatchRead,
    TournamentRead,
    VenueRead,
)
from app.services.tournament_seed import KNOCKOUT_STAGES, WORLD_CUP_2026_GROUPS

STAGES = ["Group Stage", *KNOCKOUT_STAGES]


def get_tournament(db: Session) -> TournamentRead:
    tournament = db.scalar(select(Tournament).where(Tournament.name == "FIFA World Cup 2026"))
    if not tournament:
        raise ValueError("Tournament is not initialized")
    return TournamentRead(
        id=tournament.id,
        name=tournament.name,
        season=tournament.season,
        host_countries=tournament.host_countries,
        stages=STAGES,
        groups=list(WORLD_CUP_2026_GROUPS.keys()),
    )


def list_tournament_matches(
    db: Session,
    stage: str | None = None,
    group: str | None = None,
    team: str | None = None,
    status: str | None = None,
) -> list[TournamentMatchRead]:
    stmt = match_query()
    if stage:
        stmt = stmt.where(TournamentMatch.stage == stage)
    if group:
        stmt = stmt.where(TournamentMatch.group == group.replace("Group ", ""))
    if status:
        stmt = stmt.where(TournamentMatch.status == status)
    if team:
        team_row = db.scalar(select(Team).where(Team.name.ilike(team.strip())))
        if team_row:
            stmt = stmt.where(or_(TournamentMatch.home_team_id == team_row.id, TournamentMatch.away_team_id == team_row.id))
        else:
            return []
    matches = list(db.scalars(stmt.order_by(TournamentMatch.kickoff_time_utc.asc().nulls_last(), TournamentMatch.id)).all())
    return [to_match_read(db, match, include_prediction=True) for match in matches]


def get_match_detail(db: Session, match_id: int) -> MatchDetailRead | None:
    match = db.scalar(match_query().where(TournamentMatch.id == match_id))
    if not match:
        return None
    base = to_match_read(db, match, include_prediction=True)
    events = [
        to_event_read(event)
        for event in db.scalars(select(MatchEvent).where(MatchEvent.match_id == match.id).order_by(MatchEvent.minute)).all()
    ]
    stats = db.scalar(select(MatchStatsSnapshot).where(MatchStatsSnapshot.match_id == match.id))
    standings = build_group_standings(db, match.group) if match.group else []
    unavailable = []
    if not events:
        unavailable.append("Timeline events")
    if not stats:
        unavailable.append("Match statistics")
    if not match.venue:
        unavailable.append("Venue details")
    if not match.kickoff_time_utc:
        unavailable.append("Kickoff time")
    return MatchDetailRead(
        **base.model_dump(),
        events=events,
        stats=stats.stats if stats else None,
        standings=standings,
        unavailable_fields=unavailable,
    )


def get_next_match(db: Session) -> TournamentMatchRead | None:
    now = datetime.now(timezone.utc)
    match = db.scalar(
        match_query()
        .where(
            TournamentMatch.status == "scheduled",
            TournamentMatch.kickoff_time_utc.is_not(None),
            TournamentMatch.kickoff_time_utc >= now,
        )
        .order_by(TournamentMatch.kickoff_time_utc.asc())
        .limit(1)
    )
    return to_match_read(db, match, include_prediction=True) if match else None


def build_group_standings(db: Session, group: str | None = None) -> list[StandingRead]:
    groups = [group.replace("Group ", "")] if group else list(WORLD_CUP_2026_GROUPS)
    rows: list[StandingRead] = []
    for group_key in groups:
        label = group_key if group_key.startswith("Group ") else f"Group {group_key}"
        team_names = WORLD_CUP_2026_GROUPS.get(label, [])
        teams = {team.name: team for team in db.scalars(select(Team).where(Team.name.in_(team_names))).all()}
        table = {
            name: {"played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "form": []}
            for name in team_names
            if name in teams
        }
        matches = db.scalars(
            select(TournamentMatch)
            .options(joinedload(TournamentMatch.home_team), joinedload(TournamentMatch.away_team))
            .where(TournamentMatch.stage == "Group Stage", TournamentMatch.group == group_key.replace("Group ", ""))
        ).all()
        for match in matches:
            if match.status != "finished" or match.home_score is None or match.away_score is None or not match.home_team or not match.away_team:
                continue
            apply_result(table[match.home_team.name], match.home_score, match.away_score)
            apply_result(table[match.away_team.name], match.away_score, match.home_score)
        for name, stats in table.items():
            rows.append(
                StandingRead(
                    group=label,
                    team=to_team_read(teams[name]),
                    played=stats["played"],
                    won=stats["won"],
                    drawn=stats["drawn"],
                    lost=stats["lost"],
                    goals_for=stats["gf"],
                    goals_against=stats["ga"],
                    goal_difference=stats["gf"] - stats["ga"],
                    points=stats["won"] * 3 + stats["drawn"],
                    form="".join(stats["form"][-5:]) or "-",
                )
            )
    return sorted(rows, key=lambda row: (row.group, -row.points, -row.goal_difference, -row.goals_for, row.team.name))


def match_query():
    return select(TournamentMatch).options(
        joinedload(TournamentMatch.home_team),
        joinedload(TournamentMatch.away_team),
        joinedload(TournamentMatch.winner_team),
        joinedload(TournamentMatch.venue),
    )


def to_match_read(db: Session, match: TournamentMatch, include_prediction: bool = False) -> TournamentMatchRead:
    prediction = get_or_create_match_prediction(db, match) if include_prediction else None
    return TournamentMatchRead(
        id=match.id,
        stage=match.stage,
        group=match.group,
        home_team=to_team_read(match.home_team) if match.home_team else None,
        away_team=to_team_read(match.away_team) if match.away_team else None,
        venue=VenueRead.model_validate(match.venue) if match.venue else None,
        kickoff_time_utc=match.kickoff_time_utc,
        status=match.status,
        home_score=match.home_score,
        away_score=match.away_score,
        extra_time_score=match.extra_time_score,
        penalty_score=match.penalty_score,
        winner_team=to_team_read(match.winner_team) if match.winner_team else None,
        result_text=result_text(match),
        data_quality=data_quality(match),
        prediction=prediction,
    )


def get_or_create_match_prediction(db: Session, match: TournamentMatch) -> MatchPredictionRead | None:
    if not match.home_team or not match.away_team:
        return None
    existing = db.scalar(select(MatchPrediction).where(MatchPrediction.match_id == match.id))
    if existing:
        return prediction_to_read(existing)
    prediction = predict_match(
        db,
        match.home_team,
        match.away_team,
        "neutral" if not match.venue else "home",
        (match.kickoff_time_utc.date() if match.kickoff_time_utc else datetime.now(timezone.utc).date()),
    )
    top_score = prediction.most_likely_scorelines[0].score if prediction.most_likely_scorelines else "1-1"
    home_score, away_score = [int(part) for part in top_score.split("-")]
    row = MatchPrediction(
        match_id=match.id,
        home_win_probability=prediction.team_a_win_probability,
        draw_probability=prediction.draw_probability,
        away_win_probability=prediction.team_b_win_probability,
        predicted_home_score=home_score,
        predicted_away_score=away_score,
        confidence=prediction.confidence,
        explanation=f"Estimate only. {prediction.explanation}",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return prediction_to_read(row)


def prediction_to_read(prediction: MatchPrediction) -> MatchPredictionRead:
    return MatchPredictionRead(
        home_win_probability=prediction.home_win_probability,
        draw_probability=prediction.draw_probability,
        away_win_probability=prediction.away_win_probability,
        predicted_home_score=prediction.predicted_home_score,
        predicted_away_score=prediction.predicted_away_score,
        confidence=prediction.confidence,
        explanation=prediction.explanation,
        generated_at=prediction.generated_at,
    )


def to_event_read(event: MatchEvent) -> MatchEventRead:
    return MatchEventRead(
        minute=event.minute,
        stoppage_time=event.stoppage_time,
        event_type=event.event_type,
        team=to_team_read(event.team) if event.team else None,
        player_name=event.player_name,
        assist_player_name=event.assist_player_name,
        card_type=event.card_type,
        description=event.description,
    )


def to_team_read(team: Team) -> MatchTeamRead:
    return MatchTeamRead(id=team.id, name=team.name, fifa_code=team.fifa_code, flag_url=None)


def result_text(match: TournamentMatch) -> str | None:
    if match.status != "finished" or match.home_score is None or match.away_score is None or not match.home_team or not match.away_team:
        return None
    score = f"{match.home_team.name} {match.home_score}-{match.away_score} {match.away_team.name}"
    if match.penalty_score:
        winner = match.winner_team.name if match.winner_team else "Winner"
        return f"{score}, {winner} won {match.penalty_score} on penalties"
    if match.home_score == match.away_score:
        return f"{score}, draw"
    winner = match.home_team.name if match.home_score > match.away_score else match.away_team.name
    loser = match.away_team.name if match.home_score > match.away_score else match.home_team.name
    return f"{winner} won {max(match.home_score, match.away_score)}-{min(match.home_score, match.away_score)} against {loser}"


def data_quality(match: TournamentMatch) -> str:
    if match.source == "sports-api":
        return "Live sports API data."
    settings = get_settings()
    if not settings.sports_api_base_url or not settings.sports_api_key:
        return "Data not available yet. Configure SPORTS_API_BASE_URL and SPORTS_API_KEY to import live fixture details."
    return "Data not available yet. Sports API is configured, but no live fixture details matched this record."


def apply_result(stats: dict[str, object], goals_for: int, goals_against: int) -> None:
    stats["played"] += 1
    stats["gf"] += goals_for
    stats["ga"] += goals_against
    if goals_for > goals_against:
        stats["won"] += 1
        stats["form"].append("W")
    elif goals_for == goals_against:
        stats["drawn"] += 1
        stats["form"].append("D")
    else:
        stats["lost"] += 1
        stats["form"].append("L")
