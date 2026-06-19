from app.ml.elo import elo_expected_goals, elo_probabilities
from app.ml.poisson_model import poisson_outcome_probabilities, top_scorelines
from app.ml.xgboost_model import XGBoostMatchClassifier


def normalize(probabilities: dict[str, float]) -> dict[str, float]:
    total = sum(probabilities.values())
    if total <= 0:
        return {
            "team_a_win_probability": 1 / 3,
            "draw_probability": 1 / 3,
            "team_b_win_probability": 1 / 3,
        }
    return {key: value / total for key, value in probabilities.items()}


def ensemble_predict(
    features: dict[str, float],
    classifier: XGBoostMatchClassifier,
) -> dict[str, float | list[dict[str, float | str]]]:
    xgboost_probs = classifier.predict_proba(features)
    elo_probs = elo_probabilities(features["elo_diff"])
    xg_a, xg_b = elo_expected_goals(features["elo_diff"], features["recent_form_diff"])
    poisson_probs = poisson_outcome_probabilities(xg_a, xg_b)

    weighted = {
        key: (
            xgboost_probs[key] * 0.5
            + elo_probs[key] * 0.3
            + poisson_probs[key] * 0.2
        )
        for key in elo_probs
    }
    normalized = normalize(weighted)
    return {
        **{key: round(value, 4) for key, value in normalized.items()},
        "expected_goals_team_a": xg_a,
        "expected_goals_team_b": xg_b,
        "most_likely_scorelines": top_scorelines(xg_a, xg_b, count=5),
    }
