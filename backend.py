from __future__ import annotations

import io
import json
import os
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, Security, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from PIL import Image

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
    HAS_SLOWAPI = True
except ImportError:
    HAS_SLOWAPI = False

import config
from src.logging_config import setup_logger
from src.main import InvoicePipeline

logger = setup_logger("ledgerlens.backend")

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[config.RATE_LIMIT]) if HAS_SLOWAPI else None

app = FastAPI(
    title="AI Invoice Intelligence API",
    version="1.0.0",
    docs_url=None if config.IS_PRODUCTION else "/docs",
    redoc_url=None if config.IS_PRODUCTION else "/redoc",
)

if limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Optional API Key Authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> Optional[str]:
    """If config.API_KEY is defined, require a matching key in X-API-Key header."""
    if not config.API_KEY:
        return None
    if not api_key or api_key != config.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key."
        )
    return api_key

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s\n%s", request.method, request.url.path, exc, traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

# Initialize Invoice Pipeline
pipeline = InvoicePipeline(config.MODEL_PATH)

# Persistent Invoices Store
STORE_PATH = config.INVOICES_STORE_PATH
STORE_PATH.parent.mkdir(parents=True, exist_ok=True)

try:
    processed_invoices: List[Dict[str, Any]] = (
        json.loads(STORE_PATH.read_text(encoding="utf-8")) if STORE_PATH.exists() else []
    )
except (OSError, json.JSONDecodeError) as exc:
    logger.error("Failed to load existing invoices from %s: %s", STORE_PATH, exc)
    processed_invoices = []


def persist_invoices() -> None:
    """Safely persist processed invoices using an atomic write (temp file + rename)."""
    tmp_path = STORE_PATH.with_suffix(".tmp")
    try:
        tmp_path.write_text(json.dumps(processed_invoices, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(STORE_PATH)
    except OSError as exc:
        logger.error("Failed to atomically persist invoices: %s", exc)
        tmp_path.unlink(missing_ok=True)


def result_for_inventory(result: Dict[str, Any], filename: str = "") -> Dict[str, Any]:
    subtotal = result.get("subtotal") or 0
    tax = result.get("tax") or 0
    total = result.get("total") or 0
    expected = subtotal + tax
    return {
        **result,
        "invoice_number": result.get("invoice_number") or "Not extracted",
        "vendor": result.get("vendor") or "Not extracted",
        "client": result.get("client") or "Not extracted",
        "expected_total": expected,
        "difference": total - expected,
        "anomaly": result.get("final_decision") == "ANOMALY",
        "score": result.get("anomaly_score", 0),
        "anomaly_text": (
            result.get("rule_anomalies", ["Validated"])[0]
            if result.get("rule_anomalies")
            else "Validated"
        ),
        "json_file": filename,
    }


def validate_file_content(content: bytes, suffix: str) -> None:
    """Validate magic bytes / content structure to prevent malicious disguised files."""
    if suffix == ".json":
        try:
            json.loads(content.decode("utf-8"))
        except Exception as err:
            raise ValueError(f"Uploaded JSON is malformed or invalid UTF-8: {err}")
    elif suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        try:
            img = Image.open(io.BytesIO(content))
            img.verify()
        except Exception as err:
            raise ValueError(f"Uploaded file claims to be an image but is invalid: {err}")


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/invoices", dependencies=[Depends(verify_api_key)])
def invoices() -> List[Dict[str, Any]]:
    return processed_invoices


@app.get("/api/invoices/{invoice_number}", dependencies=[Depends(verify_api_key)])
def invoice(invoice_number: str) -> Dict[str, Any]:
    return next(
        (item for item in processed_invoices if str(item.get("invoice_number")) == invoice_number),
        {}
    )


@app.get("/api/statistics", dependencies=[Depends(verify_api_key)])
def statistics() -> Dict[str, Any]:
    total = len(processed_invoices)
    anomalous = sum(1 for item in processed_invoices if item.get("anomaly"))
    return {
        "total": total,
        "normal": total - anomalous,
        "anomalous": anomalous,
        "anomaly_rate": round(anomalous / total * 100, 2) if total else 0,
        "distribution": [],
    }


@app.get("/api/models/performance", dependencies=[Depends(verify_api_key)])
def model_performance() -> List[Dict[str, Any]]:
    report = config.MODEL_COMPARISON_PATH
    if not report.exists():
        return []
    import pandas as pd

    try:
        frame = pd.read_csv(report)
        split = frame[frame.get("split", "train_holdout") == "test"] if "split" in frame else frame
        return [
            {
                "model": row["model"].replace("_", " ").title(),
                "accuracy": row["accuracy"],
                "precision": row["precision"],
                "recall": row["recall"],
                "f1": row["f1"],
            }
            for row in split.to_dict("records")
        ]
    except Exception as exc:
        logger.error("Failed to read model performance CSV: %s", exc)
        return []


@app.post("/api/analyze", dependencies=[Depends(verify_api_key)])
async def analyze(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    allowed_suffixes = {".json", ".png", ".jpg", ".jpeg", ".webp"}
    if suffix not in allowed_suffixes:
        return {
            "analysis_status": "UNABLE_TO_ANALYZE",
            "analysis_message": f"Unsupported file extension '{suffix}'. Allowed: {', '.join(sorted(allowed_suffixes))}",
        }

    # Stream content with size limitation to avoid memory exhaustion
    content = bytearray()
    chunk_size = 64 * 1024
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > config.MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                detail=f"File exceeds maximum allowed upload size of {config.MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
            )

    content_bytes = bytes(content)
    if not content_bytes:
        return {
            "analysis_status": "UNABLE_TO_ANALYZE",
            "analysis_message": "Uploaded file is empty.",
        }

    # Verify file payload integrity
    try:
        validate_file_content(content_bytes, suffix)
    except ValueError as exc:
        return {
            "analysis_status": "UNABLE_TO_ANALYZE",
            "analysis_message": str(exc),
        }

    # Create temporary file safely
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(content_bytes)
        temp_path = Path(handle.name)

    try:
        logger.info("Processing invoice '%s' (%s, %d bytes)", file.filename, suffix, len(content_bytes))
        result = pipeline.process_json(temp_path) if suffix == ".json" else pipeline.process_image(temp_path)
        result = result_for_inventory(result, file.filename or "")
        result["source"] = "api"
        if result.get("analysis_status") == "UNABLE_TO_ANALYZE":
            logger.warning("Invoice analysis could not extract fields for '%s': %s", file.filename, result.get("analysis_message"))
            return result

        processed_invoices.insert(0, result)
        persist_invoices()
        return result
    except Exception as exc:
        logger.exception("Error processing invoice file '%s': %s", file.filename, exc)
        return {
            "analysis_status": "UNABLE_TO_ANALYZE",
            "analysis_message": f"We could not analyze this file: {exc}",
        }
    finally:
        temp_path.unlink(missing_ok=True)
