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


def test_tournament_metadata_endpoint(client):
    response = client.get("/tournament")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "FIFA World Cup 2026"
    assert "Group Stage" in payload["stages"]
    assert "Group C" in payload["groups"]


def test_matches_endpoint_returns_group_matches(client):
    response = client.get("/matches?stage=Group%20Stage&group=Group%20C")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 6
    teams = {match["home_team"]["name"] for match in payload if match["home_team"]}
    assert "Brazil" in teams


def test_match_detail_has_unavailable_event_state(client):
    matches = client.get("/matches?stage=Group%20Stage&group=Group%20C").json()
    response = client.get(f"/matches/{matches[0]['id']}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["events"] == []
    assert "Timeline events" in payload["unavailable_fields"]


def test_worldcup_api_routes_do_not_require_frontend_key(client):
    response = client.get("/api/worldcup/matches")
    assert response.status_code == 200
    assert response.json() == []

    detail = client.get("/api/worldcup/match/12345")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["fixtureId"] == 12345
    assert "match info" in payload["unavailableFields"]
    assert "Data not available yet" in payload["dataQuality"]


def test_worldcup_internal_prediction_falls_back_without_api_data(client):
    response = client.get("/api/worldcup/prediction/12345")
    assert response.status_code == 200
    payload = response.json()
    assert payload["fixtureId"] == 12345
    assert payload["homeWinProbability"] == 34.0
    assert payload["drawProbability"] == 32.0
    assert payload["awayWinProbability"] == 34.0
    assert payload["source"] == "internal-standings"
