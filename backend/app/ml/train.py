from datetime import datetime, timezone
from pathlib import Path

from sklearn.metrics import accuracy_score, log_loss
from sqlalchemy.orm import Session

from app.config import get_settings
from app.ml.features import FEATURE_COLUMNS, build_training_frame
from app.ml.xgboost_model import XGBoostMatchClassifier
from app.models.entities import ModelRun


def train_model(db: Session) -> dict[str, object]:
    settings = get_settings()
    rows, labels = build_training_frame(db)
    if not rows:
        raise ValueError("No matches are available for training")

    started = datetime.now(timezone.utc)
    model_run = ModelRun(
        model_name="world-cup-outcome-classifier",
        model_version=settings.xgboost_model_version,
        training_started_at=started,
        metrics={},
    )
    db.add(model_run)
    db.commit()
    db.refresh(model_run)

    classifier = XGBoostMatchClassifier(Path(settings.model_dir) / "xgboost_match_classifier.joblib")
    metadata = classifier.train(rows, labels)
    probabilities = [normalized_probability_row(classifier.predict_proba(row)) for row in rows]
    predictions = [max(range(3), key=lambda index: probs[index]) for probs in probabilities]
    metrics = {
        "accuracy": round(float(accuracy_score(labels, predictions)), 4),
        "log_loss": round(float(log_loss(labels, probabilities, labels=[0, 1, 2])), 4),
        "training_dataset_size": len(rows),
    }

    mlflow_run_id = None
    try:
        import mlflow

        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        with mlflow.start_run(run_name=settings.xgboost_model_version) as run:
            mlflow_run_id = run.info.run_id
            mlflow.log_params({"model_version": settings.xgboost_model_version, "features": ",".join(FEATURE_COLUMNS)})
            mlflow.log_metrics({key: float(value) for key, value in metrics.items() if isinstance(value, (float, int))})
            mlflow.log_artifact(str(classifier.model_path))
    except Exception:
        mlflow_run_id = "mlflow-unavailable-demo-run"

    model_run.training_completed_at = datetime.now(timezone.utc)
    model_run.metrics = {**metrics, **metadata}
    model_run.mlflow_run_id = mlflow_run_id
    db.commit()

    return {
        "model_version": settings.xgboost_model_version,
        "metrics": model_run.metrics,
        "mlflow_run_id": mlflow_run_id,
    }


def normalized_probability_row(probabilities: dict[str, float]) -> list[float]:
    row = [
        probabilities["team_a_win_probability"],
        probabilities["draw_probability"],
        probabilities["team_b_win_probability"],
    ]
    total = sum(row)
    if total <= 0:
        return [1 / 3, 1 / 3, 1 / 3]
    return [value / total for value in row]
