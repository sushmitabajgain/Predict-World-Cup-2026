from typing import Any, TypedDict

from sqlalchemy.orm import Session

from app.models.entities import Team
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.cache import CacheService


class PredictionAgentState(TypedDict, total=False):
    request: PredictionRequest
    db: Session
    cache: CacheService
    team_a: Team
    team_b: Team
    features: dict[str, float]
    response: PredictionResponse
    prediction_cache_key: str
    cache_hit: bool
    stored_prediction_id: int
    errors: list[str]
    metadata: dict[str, Any]
