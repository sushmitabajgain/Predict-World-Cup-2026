def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_teams_endpoint_returns_participating_countries_only(client):
    response = client.get("/teams")
    assert response.status_code == 200
    team_names = {team["name"] for team in response.json()}
    assert {"Brazil", "Scotland", "Argentina"}.issubset(team_names)
    assert "Mexico" in team_names
    assert "Barbados" not in team_names


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


def test_prediction_rejects_non_participant(client):
    response = client.post(
        "/predict",
        json={
            "team_a": "Brazil",
            "team_b": "Barbados",
            "venue_type": "neutral",
            "match_date": "2026-06-24",
        },
    )
    assert response.status_code == 400
    assert "not a 2026 World Cup participant" in response.json()["detail"]
