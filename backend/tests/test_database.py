from datetime import date, datetime, timezone

from sqlalchemy import select

from app.models.entities import Prediction, Team
from app.schemas.prediction import PredictionCreate, ScorelineProbability
from app.services.predictions import save_prediction


def test_database_prediction_save(db_session):
    brazil = db_session.scalar(select(Team).where(Team.name == "Brazil"))
    scotland = db_session.scalar(select(Team).where(Team.name == "Scotland"))
    payload = PredictionCreate(
        team_a_id=brazil.id,
        team_b_id=scotland.id,
        team_a="Brazil",
        team_b="Scotland",
        match_date=date(2026, 6, 24),
        team_a_win_probability=0.58,
        draw_probability=0.24,
        team_b_win_probability=0.18,
        expected_goals_team_a=1.7,
        expected_goals_team_b=0.9,
        most_likely_scorelines=[ScorelineProbability(score="1-0", probability=0.13)],
        confidence="medium",
        explanation="Demo explanation",
        model_version="xgboost-v1",
        created_at=datetime.now(timezone.utc),
    )
    saved = save_prediction(db_session, payload)
    assert saved.id is not None
    assert db_session.get(Prediction, saved.id).team_a_win_probability == 0.58
