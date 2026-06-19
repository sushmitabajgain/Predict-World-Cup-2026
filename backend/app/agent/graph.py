from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agent.nodes import (
    build_features,
    check_prediction_cache,
    fetch_team_records,
    run_prediction_model,
    store_prediction,
    validate_input,
)
from app.agent.state import PredictionAgentState
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.cache import CacheService


def build_prediction_graph():
    graph = StateGraph(PredictionAgentState)
    graph.add_node("validate_input", validate_input)
    graph.add_node("fetch_team_records", fetch_team_records)
    graph.add_node("build_features", build_features)
    graph.add_node("check_prediction_cache", check_prediction_cache)
    graph.add_node("run_prediction_model", run_prediction_model)
    graph.add_node("store_prediction", store_prediction)
    graph.set_entry_point("validate_input")
    graph.add_edge("validate_input", "fetch_team_records")
    graph.add_edge("fetch_team_records", "build_features")
    graph.add_edge("build_features", "check_prediction_cache")
    graph.add_edge("check_prediction_cache", "run_prediction_model")
    graph.add_edge("run_prediction_model", "store_prediction")
    graph.add_edge("store_prediction", END)
    return graph.compile()


prediction_graph = build_prediction_graph()


def run_prediction_workflow(db: Session, request: PredictionRequest, cache: CacheService | None = None) -> PredictionResponse:
    state: PredictionAgentState = {
        "db": db,
        "request": request,
        "cache": cache or CacheService(),
        "metadata": {"workflow": "langgraph-deterministic-v1"},
    }
    result = prediction_graph.invoke(state)
    return result["response"]
