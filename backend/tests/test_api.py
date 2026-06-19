def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_prediction_endpoint(client):
    response = client.post(
        "/predict",
        json={
            "team_a": "Brazil",
            "team_b": "Scotland",
            "venue_type": "neutral",
            "match_date": "2026-06-24",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["team_a"] == "Brazil"
    assert payload["team_b"] == "Scotland"
    assert round(
        payload["team_a_win_probability"] + payload["draw_probability"] + payload["team_b_win_probability"],
        4,
    ) == 1.0
    assert payload["most_likely_scorelines"]
    assert payload["model_version"] == "xgboost-v1"
