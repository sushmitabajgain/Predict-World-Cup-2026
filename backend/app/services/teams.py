from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Team
from app.services.cache import CacheService, teams_key
from app.services.world_cup_2026 import WORLD_CUP_2026_PARTICIPANTS, is_world_cup_2026_participant


def list_teams(db: Session, cache: CacheService | None = None) -> list[Team]:
    if cache:
        cached = cache.get_json(teams_key())
        if cached:
            return [Team(**team) for team in cached]

    teams_by_name = {
        team.name: team
        for team in db.scalars(select(Team).where(Team.name.in_(WORLD_CUP_2026_PARTICIPANTS))).all()
    }
    teams = [teams_by_name[name] for name in WORLD_CUP_2026_PARTICIPANTS if name in teams_by_name]
    if cache:
        cache.set_json(
            teams_key(),
            [
                {
                    "id": team.id,
                    "name": team.name,
                    "fifa_code": team.fifa_code,
                    "confederation": team.confederation,
                }
                for team in teams
            ],
            ttl_seconds=900,
        )
    return teams


def get_team_by_name(db: Session, name: str) -> Team | None:
    if not is_world_cup_2026_participant(name):
        return None
    return db.scalar(select(Team).where(Team.name.ilike(name.strip())))
