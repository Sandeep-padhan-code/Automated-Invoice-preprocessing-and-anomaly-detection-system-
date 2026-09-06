from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import pandas as pd

from .preprocessing import FEATURE_COLUMNS, create_features


class AnomalyDetector:
    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        self.model = joblib.load(self.model_path)

    def predict(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        df = pd.DataFrame([invoice])
        df = create_features(df)
        X = df.reindex(columns=FEATURE_COLUMNS, fill_value=0).astype(float).fillna(0)
        raw_prediction = int(self.model.predict(X)[0])
        # Isolation Forest uses -1 for outliers; the dashboard uses 1/0.
        prediction = 1 if raw_prediction == -1 else int(raw_prediction == 1)
        probability = None
        if hasattr(self.model, "predict_proba"):
            try:
                probability = float(self.model.predict_proba(X)[0][1])
            except Exception:
                probability = None
        return {"prediction": prediction, "probability": probability}
