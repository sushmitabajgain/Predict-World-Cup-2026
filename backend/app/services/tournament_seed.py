from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Team, Tournament, TournamentMatch
from app.services.world_cup_2026 import WORLD_CUP_2026_PARTICIPANTS


WORLD_CUP_2026_GROUPS = {
    "Group A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "Group B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "Group C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "Group D": ["United States", "Paraguay", "Australia", "Turkey"],
    "Group E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "Group F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "Group G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "Group H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "Group I": ["France", "Senegal", "Iraq", "Norway"],
    "Group J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "Group K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "Group L": ["England", "Croatia", "Ghana", "Panama"],
}

KNOCKOUT_STAGES = [
    "Round of 32",
    "Round of 16",
    "Quarter-finals",
    "Semi-finals",
    "Third-place match",
    "Final",
]


def seed_tournament_shell(db: Session) -> Tournament:
    tournament = db.scalar(select(Tournament).where(Tournament.name == "FIFA World Cup 2026"))
    if not tournament:
        tournament = Tournament(
            name="FIFA World Cup 2026",
            season="2026",
            host_countries=["Canada", "Mexico", "United States"],
        )
        db.add(tournament)
        db.flush()

    teams_by_name = {
        team.name: team
        for team in db.scalars(select(Team).where(Team.name.in_(WORLD_CUP_2026_PARTICIPANTS))).all()
    }

    for group_name, team_names in WORLD_CUP_2026_GROUPS.items():
        group_letter = group_name.replace("Group ", "")
        group_teams = [teams_by_name[name] for name in team_names if name in teams_by_name]
        for home_index in range(len(group_teams)):
            for away_index in range(home_index + 1, len(group_teams)):
                home = group_teams[home_index]
                away = group_teams[away_index]
                exists = db.scalar(
                    select(TournamentMatch)
                    .where(
                        TournamentMatch.tournament_id == tournament.id,
                        TournamentMatch.stage == "Group Stage",
                        TournamentMatch.group == group_letter,
                        TournamentMatch.home_team_id == home.id,
                        TournamentMatch.away_team_id == away.id,
                    )
                    .limit(1)
                )
                if exists:
                    continue
                db.add(
                    TournamentMatch(
                        tournament_id=tournament.id,
                        stage="Group Stage",
                        group=group_letter,
                        home_team_id=home.id,
                        away_team_id=away.id,
                        status="scheduled",
                        source="tournament-shell",
                    )
                )

    for stage in KNOCKOUT_STAGES:
        exists = db.scalar(
            select(TournamentMatch)
            .where(
                TournamentMatch.tournament_id == tournament.id,
                TournamentMatch.stage == stage,
            )
            .limit(1)
        )
        if not exists:
            db.add(TournamentMatch(tournament_id=tournament.id, stage=stage, status="scheduled", source="tournament-shell"))

    db.commit()
    return tournament
