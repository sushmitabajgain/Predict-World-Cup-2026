from collections.abc import Generator
from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.models.entities import Base, Match, Team, TeamRating
from app.services.real_dataset import seed_real_dataset

settings = get_settings()

engine_kwargs = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    engine_kwargs = {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        real_rows_inserted = 0
        if settings.use_real_dataset and settings.real_dataset_path.exists():
            real_rows_inserted = seed_real_dataset(db, settings.real_dataset_path)
        if settings.seed_demo_data and not real_rows_inserted and not db.scalar(select(Match).limit(1)):
            seed_demo_data(db)


DEMO_TEAMS = [
    ("Brazil", "BRA", "CONMEBOL", 2045, 5, 1784.1),
    ("Argentina", "ARG", "CONMEBOL", 2060, 1, 1889.0),
    ("France", "FRA", "UEFA", 2020, 2, 1851.9),
    ("England", "ENG", "UEFA", 1980, 4, 1812.3),
    ("Spain", "ESP", "UEFA", 1970, 3, 1837.2),
    ("Germany", "GER", "UEFA", 1915, 9, 1724.4),
    ("Netherlands", "NED", "UEFA", 1935, 7, 1762.0),
    ("Portugal", "POR", "UEFA", 1940, 6, 1779.5),
    ("United States", "USA", "CONCACAF", 1810, 13, 1669.4),
    ("Mexico", "MEX", "CONCACAF", 1800, 16, 1635.1),
    ("Morocco", "MAR", "CAF", 1845, 12, 1688.2),
    ("Japan", "JPN", "AFC", 1765, 18, 1614.3),
    ("Scotland", "SCO", "UEFA", 1705, 39, 1497.5),
    ("Canada", "CAN", "CONCACAF", 1690, 45, 1465.6),
]


DEMO_MATCHES = [
    ("2024-03-23", "Brazil", "England", 1, 0, "Friendly", "Wembley", "away", False),
    ("2024-06-25", "Brazil", "Scotland", 2, 0, "Demo Cup", "Neutral", "neutral", True),
    ("2024-07-09", "Argentina", "Canada", 2, 0, "Copa America", "Neutral", "neutral", True),
    ("2024-07-14", "Argentina", "Colombia", 1, 0, "Copa America", "Neutral", "neutral", True),
    ("2024-06-30", "Spain", "Georgia", 4, 1, "Euro", "Neutral", "neutral", True),
    ("2024-07-14", "Spain", "England", 2, 1, "Euro", "Neutral", "neutral", True),
    ("2024-06-21", "France", "Netherlands", 0, 0, "Euro", "Neutral", "neutral", True),
    ("2024-07-05", "Portugal", "France", 0, 0, "Euro", "Neutral", "neutral", True),
    ("2024-06-29", "Germany", "Denmark", 2, 0, "Euro", "Neutral", "neutral", True),
    ("2024-10-14", "Germany", "Netherlands", 1, 2, "Nations League", "Munich", "home", False),
    ("2024-09-10", "United States", "Mexico", 1, 1, "Friendly", "Neutral", "neutral", True),
    ("2024-10-15", "Japan", "Australia", 1, 1, "Qualifier", "Saitama", "home", False),
    ("2024-11-18", "Morocco", "Lesotho", 7, 0, "Qualifier", "Oujda", "home", False),
]


def seed_demo_data(db: Session) -> None:
    teams_by_name: dict[str, Team] = {}
    for name, code, confed, elo, fifa_rank, fifa_points in DEMO_TEAMS:
        team = db.scalar(select(Team).where(Team.name == name))
        if not team:
            team = Team(name=name, fifa_code=code, confederation=confed)
            db.add(team)
            db.flush()
        teams_by_name[name] = team
        has_rating = db.scalar(select(TeamRating).where(TeamRating.team_id == team.id).limit(1))
        if not has_rating:
            db.add(
                TeamRating(
                    team_id=team.id,
                    rating_date=date(2026, 1, 1),
                    elo_rating=float(elo),
                    fifa_rank=fifa_rank,
                    fifa_points=float(fifa_points),
                )
            )

    for match_date, team_a, team_b, score_a, score_b, competition, venue, venue_type, is_neutral in DEMO_MATCHES:
        if team_a not in teams_by_name or team_b not in teams_by_name:
            continue
        parsed_date = date.fromisoformat(match_date)
        existing_match = db.scalar(
            select(Match)
            .where(
                Match.match_date == parsed_date,
                Match.team_a_id == teams_by_name[team_a].id,
                Match.team_b_id == teams_by_name[team_b].id,
                Match.competition == competition,
            )
            .limit(1)
        )
        if existing_match:
            continue
        db.add(
            Match(
                match_date=parsed_date,
                team_a_id=teams_by_name[team_a].id,
                team_b_id=teams_by_name[team_b].id,
                score_a=score_a,
                score_b=score_b,
                competition=competition,
                venue=venue,
                venue_type=venue_type,
                is_neutral=is_neutral,
            )
        )
    db.commit()
