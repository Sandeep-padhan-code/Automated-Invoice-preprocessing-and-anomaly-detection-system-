from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "subtotal",
    "tax",
    "total",
    "tax_ratio",
    "amount_log",
    "invoice_missing",
    "date_missing",
    "vendor_missing",
    "subtotal_missing",
    "tax_missing",
    "total_missing",
    "negative_total",
]


def is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or value == ""


def clean_number(value: Any) -> Optional[float]:
    if is_missing(value):
        return None
    if isinstance(value, (int, float)) and not pd.isna(value):
        return float(value)
    s = str(value).strip()
    s = s.replace("\u00a0", " ")
    s = "".join(ch for ch in s if ch.isdigit() or ch in ".,-")
    if not s:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        if len(s.split(",")[-1]) in (1, 2):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "." in s and len(s.split(".")[-1]) == 3 and s.count(".") == 1:
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def normalize_date(value: Any) -> Optional[pd.Timestamp]:
    if is_missing(value):
        return None
    return pd.to_datetime(value, errors="coerce", dayfirst=True)


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    for col in ["invoice_number", "date", "vendor", "subtotal", "tax", "total"]:
        if col not in frame:
            frame[col] = None
    for col in ["subtotal", "tax", "total"]:
        frame[col] = pd.to_numeric(frame[col].map(clean_number), errors="coerce")
    subtotal = frame["subtotal"].fillna(0)
    denominator = subtotal.mask(subtotal == 0, np.nan)
    frame["tax_ratio"] = (frame["tax"].fillna(0) / denominator).fillna(0.0)
    frame["amount_log"] = np.log1p(frame[["subtotal", "tax", "total"]].fillna(0).abs().sum(axis=1))
    frame["invoice_missing"] = frame["invoice_number"].map(is_missing).astype(int)
    frame["date_missing"] = frame["date"].map(is_missing).astype(int)
    frame["vendor_missing"] = frame["vendor"].map(is_missing).astype(int)
    frame["subtotal_missing"] = frame["subtotal"].isna().astype(int)
    frame["tax_missing"] = frame["tax"].isna().astype(int)
    frame["total_missing"] = frame["total"].isna().astype(int)
    frame["negative_total"] = (frame["total"].fillna(0) < 0).astype(int)
    return frame


def label_anomalies(df: pd.DataFrame, tolerance: float = 0.05) -> pd.DataFrame:
    frame = df.copy()
    expected_total = frame["subtotal"].fillna(0) + frame["tax"].fillna(0)
    total = frame["total"].fillna(0)
    mismatch = (total - expected_total).abs() > tolerance
    frame["anomaly"] = (
        frame["invoice_number"].map(is_missing)
        | frame["date"].map(is_missing)
        | frame["vendor"].map(is_missing)
        | frame["subtotal"].isna()
        | frame["tax"].isna()
        | frame["total"].isna()
        | (frame["subtotal"].fillna(0) < 0)
        | (frame["tax"].fillna(0) < 0)
        | (frame["total"].fillna(0) < 0)
        | mismatch
    ).astype(int)
    frame["expected_total"] = expected_total
    frame["difference"] = total - expected_total
    frame["total_mismatch"] = mismatch.astype(int)
    return frame


def load_json_records(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        return [data]
    return []
