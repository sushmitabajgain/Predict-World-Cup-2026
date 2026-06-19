from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent.graph import run_prediction_workflow
from app.api.deps import get_cache, get_session
from app.ml.train import train_model
from app.schemas.prediction import PredictionRead, PredictionRequest, PredictionResponse
from app.schemas.team import TeamRead
from app.services.cache import CacheService
from app.services.predictions import get_prediction, list_predictions
from app.services.teams import list_teams

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/teams", response_model=list[TeamRead])
def teams(db: Session = Depends(get_session), cache: CacheService = Depends(get_cache)) -> list[TeamRead]:
    return list_teams(db, cache)


@router.post("/predict", response_model=PredictionResponse)
def predict(
    request: PredictionRequest,
    db: Session = Depends(get_session),
    cache: CacheService = Depends(get_cache),
) -> PredictionResponse:
    try:
        return run_prediction_workflow(db, request, cache)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if message.startswith("Unknown team") else 400
        raise HTTPException(status_code=status_code, detail=message) from exc


@router.get("/predictions", response_model=list[PredictionRead])
def predictions(db: Session = Depends(get_session)) -> list[PredictionRead]:
    return list_predictions(db)


@router.get("/predictions/{prediction_id}", response_model=PredictionRead)
def prediction(prediction_id: int, db: Session = Depends(get_session)) -> PredictionRead:
    item = get_prediction(db, prediction_id)
    if not item:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return item


@router.post("/train")
def train(db: Session = Depends(get_session)) -> dict[str, object]:
    try:
        return train_model(db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
