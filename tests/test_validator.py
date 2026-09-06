from src.validator import calculate_anomaly_score, get_severity, validate_invoice


def test_validator_detects_missing():
    invoice = {"invoice_number": None, "date": "2024-01-01", "vendor": "A", "subtotal": 10, "tax": 1, "total": 11}
    anomalies = validate_invoice(invoice)
    assert "Invoice number is missing" in anomalies
    assert calculate_anomaly_score(anomalies) >= 25
    assert get_severity(0) == "Normal"

