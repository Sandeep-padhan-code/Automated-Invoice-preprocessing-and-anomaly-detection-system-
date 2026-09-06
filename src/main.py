from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .anomaly_detector import AnomalyDetector
from .ocr_engine import extract_text
from .ocr_parser import parse_ocr_text
from .parser import parse_invoice
from .preprocessing import FEATURE_COLUMNS, create_features, label_anomalies
from .validator import calculate_anomaly_score, get_severity, validate_invoice


class InvoicePipeline:
    def __init__(self, model_path: str | Path = "models/random_forest.pkl"):
        self.model_path = Path(model_path)
        self.detector = AnomalyDetector(self.model_path) if self.model_path.exists() else None

    def process_invoice(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        anomalies = validate_invoice(invoice)
        score = calculate_anomaly_score(anomalies)
        severity = get_severity(score)
        ml = {"prediction": 0, "probability": None}
        if self.detector:
            ml = self.detector.predict(invoice)
        final_decision = "ANOMALY" if ml["prediction"] == 1 or anomalies else "NORMAL"
        required_values = [invoice.get(key) for key in ("invoice_number", "date", "vendor", "subtotal", "tax", "total")]
        unable = all(value is None or value == "" for value in required_values)
        return {**invoice, "rule_anomalies": anomalies, "ml_prediction": ml["prediction"], "ml_probability": ml["probability"], "anomaly_score": score, "severity": severity, "final_decision": final_decision, "analysis_status": "UNABLE_TO_ANALYZE" if unable else "ANALYZED", "analysis_message": "We could not extract invoice fields. Try a clearer image or a supported JSON schema." if unable else "Invoice fields were extracted and checked."}

    def process_json(self, json_path: str | Path) -> Dict[str, Any]:
        invoice = parse_invoice(json_path)
        result = self.process_invoice(invoice)
        result["json_path"] = str(json_path)
        return result

    def process_image(self, image_path: str | Path) -> Dict[str, Any]:
        text = extract_text(image_path)
        invoice = parse_ocr_text(text)
        result = self.process_invoice(invoice)
        if text.startswith("OCR_ERROR:"):
            result["analysis_status"] = "UNABLE_TO_ANALYZE"
            result["analysis_message"] = "OCR could not read this image. Check that Tesseract is installed and try a sharper, well-lit invoice image."
        result["ocr_text"] = text
        result["image_path"] = str(image_path)
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-data", action="store_true")
    parser.add_argument("--train", action="store_true")
    args = parser.parse_args()
    if args.prepare_data:
        print("Place InvoiceJSON files in data/raw/invoicejson/json or run the Colab download step.")
    elif args.train:
        from .train import train_models

        train_models()
    else:
        print("Use the Streamlit app via `streamlit run app.py`.")


if __name__ == "__main__":
    main()
