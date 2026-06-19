from app.ml.ensemble import normalize
from app.ml.poisson_model import poisson_outcome_probabilities, top_scorelines


def test_poisson_scoreline_probability():
    rows = top_scorelines(1.7, 0.9, count=5)
    assert len(rows) == 5
    assert rows[0]["probability"] > 0
    outcome = poisson_outcome_probabilities(1.7, 0.9)
    assert round(sum(outcome.values()), 4) == 1.0


def test_probability_normalization():
    probabilities = normalize(
        {
            "team_a_win_probability": 2.0,
            "draw_probability": 1.0,
            "team_b_win_probability": 1.0,
        }
    )
    assert probabilities["team_a_win_probability"] == 0.5
    assert sum(probabilities.values()) == 1.0
