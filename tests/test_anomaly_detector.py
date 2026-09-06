import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier

from src.anomaly_detector import AnomalyDetector
from src.preprocessing import FEATURE_COLUMNS


def test_anomaly_detector(tmp_path):
    X = pd.DataFrame([[0] * len(FEATURE_COLUMNS)], columns=FEATURE_COLUMNS)
    y = [0]
    model = DummyClassifier(strategy="most_frequent").fit(X, y)
    path = tmp_path / "m.pkl"
    joblib.dump(model, path)
    det = AnomalyDetector(path)
    out = det.predict({"invoice_number": "1", "date": "2024-01-01", "vendor": "A", "subtotal": 1, "tax": 0, "total": 1})
    assert "prediction" in out

