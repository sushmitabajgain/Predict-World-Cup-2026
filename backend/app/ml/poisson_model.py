import math


def poisson_probability(lam: float, goals: int) -> float:
    return (math.exp(-lam) * lam**goals) / math.factorial(goals)


def scoreline_distribution(expected_goals_a: float, expected_goals_b: float, max_goals: int = 5) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for goals_a in range(max_goals + 1):
        for goals_b in range(max_goals + 1):
            probability = poisson_probability(expected_goals_a, goals_a) * poisson_probability(expected_goals_b, goals_b)
            rows.append({"score": f"{goals_a}-{goals_b}", "probability": probability})
    return sorted(rows, key=lambda item: float(item["probability"]), reverse=True)


def poisson_outcome_probabilities(expected_goals_a: float, expected_goals_b: float, max_goals: int = 5) -> dict[str, float]:
    team_a = draw = team_b = 0.0
    for row in scoreline_distribution(expected_goals_a, expected_goals_b, max_goals=max_goals):
        score_a, score_b = [int(part) for part in str(row["score"]).split("-")]
        probability = float(row["probability"])
        if score_a > score_b:
            team_a += probability
        elif score_a == score_b:
            draw += probability
        else:
            team_b += probability
    total = team_a + draw + team_b
    return {
        "team_a_win_probability": team_a / total,
        "draw_probability": draw / total,
        "team_b_win_probability": team_b / total,
    }


def top_scorelines(expected_goals_a: float, expected_goals_b: float, count: int = 5) -> list[dict[str, float | str]]:
    return [
        {"score": str(row["score"]), "probability": round(float(row["probability"]), 4)}
        for row in scoreline_distribution(expected_goals_a, expected_goals_b)[:count]
    ]
