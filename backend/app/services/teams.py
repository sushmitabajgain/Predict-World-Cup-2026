from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Team
from app.services.cache import CacheService, teams_key


def list_teams(db: Session, cache: CacheService | None = None) -> list[Team]:
    if cache:
        cached = cache.get_json(teams_key())
        if cached:
            return [Team(**team) for team in cached]

    teams = list(db.scalars(select(Team).order_by(Team.name)).all())
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
    return db.scalar(select(Team).where(Team.name.ilike(name.strip())))
