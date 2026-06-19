from datetime import datetime

from app.agent.state import PredictionAgentState
from app.ml.features import build_match_features
from app.ml.predict import predict_match
from app.schemas.prediction import PredictionResponse
from app.services.cache import features_key, prediction_key
from app.services.predictions import response_to_create, save_prediction
from app.services.teams import get_team_by_name
from app.services.world_cup_2026 import is_world_cup_2026_participant


def validate_input(state: PredictionAgentState) -> PredictionAgentState:
    request = state["request"]
    if request.team_a.casefold() == request.team_b.casefold():
        raise ValueError("Team A and Team B must be different")
    if not is_world_cup_2026_participant(request.team_a):
        raise ValueError(f"{request.team_a} is not a 2026 World Cup participant")
    if not is_world_cup_2026_participant(request.team_b):
        raise ValueError(f"{request.team_b} is not a 2026 World Cup participant")
    return state


def fetch_team_records(state: PredictionAgentState) -> PredictionAgentState:
    db = state["db"]
    request = state["request"]
    team_a = get_team_by_name(db, request.team_a)
    team_b = get_team_by_name(db, request.team_b)
    if not team_a or not team_b:
        missing = request.team_a if not team_a else request.team_b
        raise ValueError(f"Unknown team: {missing}")
    return {**state, "team_a": team_a, "team_b": team_b}


def build_features(state: PredictionAgentState) -> PredictionAgentState:
    request = state["request"]
    cache = state["cache"]
    team_a = state["team_a"]
    team_b = state["team_b"]
    key = features_key(team_a.name, team_b.name, request.match_date.isoformat())
    cached = cache.get_json(key)
    if cached:
        return {**state, "features": {item: float(value) for item, value in cached.items()}}
    features = build_match_features(state["db"], team_a, team_b, request.venue_type, request.match_date)
    cache.set_json(key, features, ttl_seconds=1800)
    return {**state, "features": features}


def check_prediction_cache(state: PredictionAgentState) -> PredictionAgentState:
    request = state["request"]
    cache = state["cache"]
    team_a = state["team_a"]
    team_b = state["team_b"]
    key = prediction_key(team_a.name, team_b.name, request.match_date.isoformat())
    cached = cache.get_json(key)
    if cached:
        cached["created_at"] = datetime.fromisoformat(str(cached["created_at"]))
        return {
            **state,
            "prediction_cache_key": key,
            "cache_hit": True,
            "response": PredictionResponse(**cached),
        }
    return {**state, "prediction_cache_key": key, "cache_hit": False}


def run_prediction_model(state: PredictionAgentState) -> PredictionAgentState:
    if state.get("cache_hit"):
        return state
    request = state["request"]
    response = predict_match(
        state["db"],
        state["team_a"],
        state["team_b"],
        request.venue_type,
        request.match_date,
        features=state["features"],
    )
    state["cache"].set_json(state["prediction_cache_key"], response.model_dump(), ttl_seconds=600)
    return {**state, "response": response}


def store_prediction(state: PredictionAgentState) -> PredictionAgentState:
    if state.get("cache_hit"):
        return state
    request = state["request"]
    response = state["response"]
    prediction = save_prediction(
        state["db"],
        response_to_create(response, state["team_a"].id, state["team_b"].id, request.match_date),
    )
    return {**state, "stored_prediction_id": prediction.id}
