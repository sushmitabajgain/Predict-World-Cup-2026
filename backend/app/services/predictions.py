from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Prediction, Team
from app.schemas.prediction import PredictionCreate, PredictionRead, PredictionResponse, ScorelineProbability


def save_prediction(db: Session, payload: PredictionCreate) -> Prediction:
    prediction = Prediction(
        team_a_id=payload.team_a_id,
        team_b_id=payload.team_b_id,
        match_date=payload.match_date,
        team_a_win_probability=payload.team_a_win_probability,
        draw_probability=payload.draw_probability,
        team_b_win_probability=payload.team_b_win_probability,
        expected_goals_team_a=payload.expected_goals_team_a,
        expected_goals_team_b=payload.expected_goals_team_b,
        most_likely_scorelines=[item.model_dump() for item in payload.most_likely_scorelines],
        confidence=payload.confidence,
        explanation=payload.explanation,
        model_version=payload.model_version,
        created_at=payload.created_at,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def list_predictions(db: Session, limit: int = 50) -> list[PredictionRead]:
    predictions = db.scalars(select(Prediction).order_by(Prediction.created_at.desc()).limit(limit)).all()
    return [prediction_to_read(db, prediction) for prediction in predictions]


def get_prediction(db: Session, prediction_id: int) -> PredictionRead | None:
    prediction = db.get(Prediction, prediction_id)
    return prediction_to_read(db, prediction) if prediction else None


def prediction_to_read(db: Session, prediction: Prediction) -> PredictionRead:
    team_a = db.get(Team, prediction.team_a_id)
    team_b = db.get(Team, prediction.team_b_id)
    return PredictionRead(
        id=prediction.id,
        team_a=team_a.name if team_a else "Unknown",
        team_b=team_b.name if team_b else "Unknown",
        match_date=prediction.match_date,
        team_a_win_probability=prediction.team_a_win_probability,
        draw_probability=prediction.draw_probability,
        team_b_win_probability=prediction.team_b_win_probability,
        expected_goals_team_a=prediction.expected_goals_team_a,
        expected_goals_team_b=prediction.expected_goals_team_b,
        most_likely_scorelines=[ScorelineProbability(**item) for item in prediction.most_likely_scorelines],
        confidence=prediction.confidence,
        explanation=prediction.explanation,
        model_version=prediction.model_version,
        created_at=prediction.created_at,
    )


def response_to_create(
    response: PredictionResponse,
    team_a_id: int,
    team_b_id: int,
    match_date,
) -> PredictionCreate:
    return PredictionCreate(
        team_a_id=team_a_id,
        team_b_id=team_b_id,
        match_date=match_date,
        **response.model_dump(),
    )
