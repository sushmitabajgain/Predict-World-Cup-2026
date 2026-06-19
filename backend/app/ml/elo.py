import math


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def elo_probabilities(elo_diff: float) -> dict[str, float]:
    team_a_strength = expected_score(elo_diff, 0)
    draw = max(0.16, min(0.32, 0.28 - abs(elo_diff) / 2500))
    decisive = 1 - draw
    team_a = decisive * team_a_strength
    team_b = decisive * (1 - team_a_strength)
    total = team_a + draw + team_b
    return {
        "team_a_win_probability": team_a / total,
        "draw_probability": draw / total,
        "team_b_win_probability": team_b / total,
    }


def elo_expected_goals(elo_diff: float, form_diff: float = 0.0) -> tuple[float, float]:
    base = 1.25
    adjustment = max(-0.75, min(0.75, elo_diff / 550 + form_diff * 0.12))
    team_a_xg = max(0.2, base + adjustment)
    team_b_xg = max(0.2, base - adjustment)
    return round(team_a_xg, 2), round(team_b_xg, 2)
