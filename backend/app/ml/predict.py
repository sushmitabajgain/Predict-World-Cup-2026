from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.ml.ensemble import ensemble_predict
from app.ml.features import build_match_features
from app.ml.xgboost_model import XGBoostMatchClassifier
from app.models.entities import Team
from app.schemas.prediction import PredictionResponse, ScorelineProbability


def confidence_from_probabilities(team_a: float, draw: float, team_b: float) -> str:
    spread = max(team_a, draw, team_b) - min(team_a, draw, team_b)
    if spread >= 0.38:
        return "high"
    if spread >= 0.18:
        return "medium"
    return "low"


def explain_prediction(team_a: Team, team_b: Team, features: dict[str, float], probabilities: dict[str, float]) -> str:
    leader = team_a.name if probabilities["team_a_win_probability"] >= probabilities["team_b_win_probability"] else team_b.name
    reasons: list[str] = []
    if abs(features["elo_diff"]) >= 50:
        reasons.append("higher Elo strength")
    if abs(features["recent_form_diff"]) >= 0.2:
        reasons.append("stronger recent form")
    if abs(features["goals_scored_recent_diff"]) >= 0.2:
        reasons.append("better recent attacking output")
    if not reasons:
        reasons.append("a balanced profile across ratings and recent results")
    return f"{leader} is favored because of {', '.join(reasons)}. This MVP uses synthetic/demo data until a real data provider is connected."


def predict_match(
    db: Session,
    team_a: Team,
    team_b: Team,
    venue_type: str,
    match_date,
    classifier: XGBoostMatchClassifier | None = None,
    features: dict[str, float] | None = None,
) -> PredictionResponse:
    settings = get_settings()
    classifier = classifier or XGBoostMatchClassifier(Path(settings.model_dir) / "xgboost_match_classifier.joblib")
    features = features or build_match_features(db, team_a, team_b, venue_type, match_date)
    result = ensemble_predict(features, classifier)
    probabilities = {
        "team_a_win_probability": float(result["team_a_win_probability"]),
        "draw_probability": float(result["draw_probability"]),
        "team_b_win_probability": float(result["team_b_win_probability"]),
    }
    return PredictionResponse(
        team_a=team_a.name,
        team_b=team_b.name,
        **probabilities,
        expected_goals_team_a=float(result["expected_goals_team_a"]),
        expected_goals_team_b=float(result["expected_goals_team_b"]),
        most_likely_scorelines=[ScorelineProbability(**row) for row in result["most_likely_scorelines"]],
        confidence=confidence_from_probabilities(
            probabilities["team_a_win_probability"],
            probabilities["draw_probability"],
            probabilities["team_b_win_probability"],
        ),
        explanation=explain_prediction(team_a, team_b, features, probabilities),
        model_version=settings.xgboost_model_version,
        created_at=datetime.now(timezone.utc),
    )
