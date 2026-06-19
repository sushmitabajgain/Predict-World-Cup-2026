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
  -> real international results dataset
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

The backend creates tables and imports a real international match-results CSV on startup. Demo data remains only as a fallback if the real CSV is unavailable.

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
- `USE_REAL_DATASET`
- `REAL_DATASET_PATH`
- `TRAINING_MATCH_LIMIT`
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

## Dataset

The app now includes a real international football results CSV at `backend/app/data/international_results.csv`.
The historical dataset remains broad for model training, but the user-facing `/teams` endpoint and `/predict` workflow are filtered to the 48 participating countries in the 2026 World Cup.

Source: [`martj42/international_results`](https://github.com/martj42/international_results), downloaded from the repository's raw `results.csv`.

Imported columns:

- `date`
- `home_team`
- `away_team`
- `home_score`
- `away_score`
- `tournament`
- `city`
- `country`
- `neutral`

At import time, the backend:

- Creates teams from real national team names.
- Stores real historical matches.
- Computes Elo-style ratings from match results.
- Derives rank and points fields from those Elo ratings.
- Uses the most recent `TRAINING_MATCH_LIMIT` matches for model training. The default is `1000` so the MVP training endpoint stays responsive while PostgreSQL still stores the full imported dataset.

## Data Limitations

The match results are real, but FIFA ranking snapshots, player availability, squads, injuries, travel, rest days, betting markets, and lineup information are not connected yet. FIFA rank and points fields are currently derived from computed Elo ratings so the feature schema stays stable.

## Future Improvements

- Add a real data ingestion worker and scheduled rating updates.
- Expand model evaluation with rolling time-based validation.
- Store trained model metadata in a model registry.
- Add calibration curves and confidence intervals.
- Add optional LLM-generated explanations behind the existing deterministic explanation interface.
