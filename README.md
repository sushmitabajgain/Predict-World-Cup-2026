# World Cup Predictor

A production-shaped MVP for deterministic FIFA World Cup match prediction. The app accepts two national teams and returns win/draw probabilities, expected goals, likely scorelines, an explanation, the model version, and a prediction timestamp.

The prediction engine is statistical/ML only. The LangGraph agent orchestrates validation, data lookup, feature preparation, cache checks, model execution, explanation, and persistence.

## Architecture

```text
React UI
  -> FastAPI /predict
    -> LangGraph workflow
      -> PostgreSQL teams, ratings, matches
      -> Redis feature and prediction cache
      -> Feature builder
      -> XGBoost classifier + Elo baseline + Poisson score model
      -> Template explanation
      -> PostgreSQL prediction record
    -> JSON response

FastAPI /train
  -> demo historical data
  -> XGBoost or sklearn fallback training
  -> MLflow metrics and artifact logging
```

## Stack

- Backend: Python, FastAPI, SQLAlchemy, PostgreSQL
- Cache: Redis
- ML: pandas, scikit-learn, XGBoost, MLflow
- Agent workflow: LangGraph
- Frontend: React, Vite
- Deployment: Docker Compose

## Run With Docker

```bash
docker compose up --build
```

Services:

- Frontend: <http://localhost:3000>
- Backend: <http://localhost:8000>
- MLflow: <http://localhost:5000>
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

The backend creates tables and seeds synthetic/demo teams, ratings, and match results on startup. This keeps the MVP usable without external football API credentials.

## Environment

Copy `.env.example` if you want to run services directly:

```bash
cp .env.example .env
```

Important variables:

- `DATABASE_URL`
- `REDIS_URL`
- `MLFLOW_TRACKING_URI`
- `CORS_ORIGINS`
- `XGBOOST_MODEL_VERSION`
- `VITE_API_URL`

## API

Health:

```bash
curl http://localhost:8000/health
```

Predict:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "team_a": "Brazil",
    "team_b": "Scotland",
    "venue_type": "neutral",
    "match_date": "2026-06-24"
  }'
```

Example response:

```json
{
  "team_a": "Brazil",
  "team_b": "Scotland",
  "team_a_win_probability": 0.58,
  "draw_probability": 0.24,
  "team_b_win_probability": 0.18,
  "expected_goals_team_a": 1.7,
  "expected_goals_team_b": 0.9,
  "most_likely_scorelines": [
    { "score": "1-0", "probability": 0.13 }
  ],
  "confidence": "medium",
  "explanation": "Brazil is favored because of higher Elo strength...",
  "model_version": "xgboost-v1",
  "created_at": "2026-06-18T12:00:00Z"
}
```

Train:

```bash
curl -X POST http://localhost:8000/train
```

Training logs model metadata, dataset size, features, accuracy, log loss, and the serialized classifier artifact to MLflow when the MLflow service is reachable.

## Local Development

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
```

Frontend:

```bash
cd frontend
npm install
npm run dev
npm test
```

## Data Limitations

The included dataset is synthetic/demo data and is intentionally small. Real production use should plug in a reliable match-results provider, up-to-date Elo or SPI-style ratings, FIFA ranking snapshots, squad availability, travel/rest data, and tournament context.

## Future Improvements

- Add a real data ingestion worker and scheduled rating updates.
- Expand model evaluation with rolling time-based validation.
- Store trained model metadata in a model registry.
- Add calibration curves and confidence intervals.
- Add optional LLM-generated explanations behind the existing deterministic explanation interface.
