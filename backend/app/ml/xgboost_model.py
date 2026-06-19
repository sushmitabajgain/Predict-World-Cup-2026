from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.features import FEATURE_COLUMNS


class XGBoostMatchClassifier:
    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self.model = None

    def train(self, rows: list[dict[str, float]], labels: list[int]) -> dict[str, float | int | str]:
        x = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
        y = pd.Series(labels)
        if len(set(labels)) >= 3 and len(labels) >= 6:
            try:
                from xgboost import XGBClassifier

                model = XGBClassifier(
                    n_estimators=50,
                    max_depth=3,
                    learning_rate=0.08,
                    objective="multi:softprob",
                    eval_metric="mlogloss",
                    random_state=42,
                )
                model.fit(x, y)
                model_name = "XGBClassifier"
            except Exception:
                model = self._fallback_model(x, y)
                model_name = "LogisticRegressionFallback"
        else:
            model = self._fallback_model(x, y)
            model_name = "LogisticRegressionFallback"

        self.model = model
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, self.model_path)
        return {"training_dataset_size": len(rows), "feature_count": len(FEATURE_COLUMNS), "estimator": model_name}

    def _fallback_model(self, x: pd.DataFrame, y: pd.Series) -> Pipeline:
        model = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(max_iter=500, random_state=42)),
            ]
        )
        model.fit(x, y)
        return model

    def load(self) -> None:
        if self.model is None and self.model_path.exists():
            self.model = joblib.load(self.model_path)

    def predict_proba(self, features: dict[str, float]) -> dict[str, float]:
        self.load()
        if self.model is None:
            return {"team_a_win_probability": 0.42, "draw_probability": 0.28, "team_b_win_probability": 0.30}

        frame = pd.DataFrame([features], columns=FEATURE_COLUMNS)
        probabilities = self.model.predict_proba(frame)[0]
        classes = list(getattr(self.model, "classes_", []))
        if not classes and hasattr(self.model, "named_steps"):
            classes = list(self.model.named_steps["classifier"].classes_)
        by_class = {int(label): float(probabilities[index]) for index, label in enumerate(classes)}
        return {
            "team_a_win_probability": by_class.get(0, 0.0),
            "draw_probability": by_class.get(1, 0.0),
            "team_b_win_probability": by_class.get(2, 0.0),
        }
