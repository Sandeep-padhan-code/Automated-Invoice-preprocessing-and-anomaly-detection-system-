import pandas as pd

from src.preprocessing import create_features, label_anomalies


def test_preprocessing_features():
    df = pd.DataFrame([{"invoice_number": "1", "date": "2024-01-01", "vendor": "A", "subtotal": "100", "tax": "10", "total": "110"}])
    out = label_anomalies(create_features(df))
    assert out.loc[0, "anomaly"] == 0

