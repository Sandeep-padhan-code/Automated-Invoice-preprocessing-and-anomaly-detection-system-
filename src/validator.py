from __future__ import annotations

from typing import Any, Dict, List

from .preprocessing import clean_number, is_missing


def validate_invoice(invoice: Dict[str, Any]) -> List[str]:
    anomalies: List[str] = []
    for key, label in [("invoice_number", "Invoice number is missing"), ("date", "Invoice date is missing"), ("vendor", "Vendor is missing"), ("subtotal", "Subtotal is missing"), ("tax", "Tax is missing"), ("total", "Total is missing")]:
        if is_missing(invoice.get(key)):
            anomalies.append(label)
    subtotal = clean_number(invoice.get("subtotal"))
    tax = clean_number(invoice.get("tax"))
    total = clean_number(invoice.get("total"))
    if subtotal is not None and subtotal < 0:
        anomalies.append("Subtotal is negative")
    if tax is not None and tax < 0:
        anomalies.append("Tax is negative")
    if total is not None and total < 0:
        anomalies.append("Total is negative")
    if subtotal is not None and tax is not None and total is not None:
        if abs(total - (subtotal + tax)) > 0.05:
            anomalies.append("Total does not match subtotal + tax")
    return anomalies


def calculate_anomaly_score(anomalies: List[str]) -> int:
    score = 0
    for anomaly in anomalies:
        if "missing" in anomaly.lower():
            score += 25
        elif "does not match" in anomaly.lower():
            score += 50
        elif "negative" in anomaly.lower():
            score += 40
    return min(score, 100)


def get_severity(score: int) -> str:
    if score == 0:
        return "Normal"
    if score <= 39:
        return "Low"
    if score <= 69:
        return "Medium"
    return "High"
