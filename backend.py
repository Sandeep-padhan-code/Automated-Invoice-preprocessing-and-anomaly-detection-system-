from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.main import InvoicePipeline


app = FastAPI(title="AI Invoice Intelligence API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
pipeline = InvoicePipeline("models/logistic_regression.pkl")
STORE_PATH = Path("outputs/predictions/processed_invoices.json")
STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
try:
    processed_invoices: List[Dict[str, Any]] = json.loads(STORE_PATH.read_text(encoding="utf-8")) if STORE_PATH.exists() else []
except (OSError, json.JSONDecodeError):
    processed_invoices = []


def persist_invoices() -> None:
    STORE_PATH.write_text(json.dumps(processed_invoices, ensure_ascii=False, indent=2), encoding="utf-8")


def result_for_inventory(result: Dict[str, Any], filename: str = "") -> Dict[str, Any]:
    subtotal = result.get("subtotal") or 0
    tax = result.get("tax") or 0
    total = result.get("total") or 0
    expected = subtotal + tax
    return {**result, "invoice_number": result.get("invoice_number") or "Not extracted", "vendor": result.get("vendor") or "Not extracted", "client": result.get("client") or "Not extracted", "expected_total": expected, "difference": total - expected, "anomaly": result.get("final_decision") == "ANOMALY", "score": result.get("anomaly_score", 0), "anomaly_text": result.get("rule_anomalies", ["Validated"])[0] if result.get("rule_anomalies") else "Validated", "json_file": filename}


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/invoices")
def invoices() -> List[Dict[str, Any]]:
    return processed_invoices


@app.get("/api/invoices/{invoice_number}")
def invoice(invoice_number: str) -> Dict[str, Any]:
    return next((item for item in processed_invoices if item.get("invoice_number") == invoice_number), {})


@app.get("/api/statistics")
def statistics() -> Dict[str, Any]:
    total = len(processed_invoices)
    anomalous = sum(1 for item in processed_invoices if item.get("anomaly"))
    return {"total": total, "normal": total - anomalous, "anomalous": anomalous, "anomaly_rate": round(anomalous / total * 100, 2) if total else 0, "distribution": []}


@app.get("/api/models/performance")
def model_performance() -> List[Dict[str, Any]]:
    report = Path("outputs/reports/model_comparison.csv")
    if not report.exists():
        return []
    import pandas as pd

    frame = pd.read_csv(report)
    split = frame[frame.get("split", "train_holdout") == "test"] if "split" in frame else frame
    return [{"model": row["model"].replace("_", " ").title(), "accuracy": row["accuracy"], "precision": row["precision"], "recall": row["recall"], "f1": row["f1"]} for row in split.to_dict("records")]


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)) -> Dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".json", ".png", ".jpg", ".jpeg", ".webp"}:
        return {"analysis_status": "UNABLE_TO_ANALYZE", "analysis_message": "This file type is not supported. Upload JSON, PNG, JPG, or JPEG."}
    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    try:
        result = pipeline.process_json(temp_path) if suffix == ".json" else pipeline.process_image(temp_path)
        result = result_for_inventory(result, file.filename or "")
        result["source"] = "api"
        if result.get("analysis_status") == "UNABLE_TO_ANALYZE":
            return result
        processed_invoices.insert(0, result)
        persist_invoices()
        return result
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"analysis_status": "UNABLE_TO_ANALYZE", "analysis_message": f"We could not analyze this file: {exc}"}
    finally:
        temp_path.unlink(missing_ok=True)
