from __future__ import annotations

import os
from pathlib import Path
from typing import List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT_DIR = Path(__file__).resolve().parent

ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION: bool = ENVIRONMENT == "production"

HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8000"))
WORKERS: int = int(os.getenv("WORKERS", "1"))

_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000"
)
ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]

MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))  # 10 MB default
RATE_LIMIT: str = os.getenv("RATE_LIMIT", "30/minute")
API_KEY: str = os.getenv("API_KEY", "").strip()

MODEL_PATH: Path = ROOT_DIR / os.getenv("MODEL_PATH", "models/logistic_regression.pkl")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

INVOICES_STORE_PATH: Path = ROOT_DIR / os.getenv("INVOICES_STORE_PATH", "outputs/predictions/processed_invoices.json")
MODEL_COMPARISON_PATH: Path = ROOT_DIR / os.getenv("MODEL_COMPARISON_PATH", "outputs/reports/model_comparison.csv")
