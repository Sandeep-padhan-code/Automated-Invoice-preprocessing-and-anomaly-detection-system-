from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .parser import parse_invoice
from .preprocessing import FEATURE_COLUMNS, create_features, label_anomalies, load_json_records


ROOT = Path(__file__).resolve().parents[1]


def demo_records(size: int = 320, seed: int = 42) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(seed)
    records: List[Dict[str, Any]] = []
    for index in range(size):
        subtotal = round(float(rng.uniform(80, 6000)), 2)
        tax = round(subtotal * float(rng.choice([.05, .1, .15, .2])), 2)
        total = round(subtotal + tax, 2)
        record: Dict[str, Any] = {"invoice_number": f"DEMO-{index + 1:04d}", "date": "2024-01-15", "vendor": f"Vendor {index % 18 + 1}", "subtotal": subtotal, "tax": tax, "total": total}
        if index % 5 == 0:
            anomaly_type = index % 4
            if anomaly_type == 0:
                record["vendor"] = None
            elif anomaly_type == 1:
                record["total"] = round(total + rng.uniform(20, 400), 2)
            elif anomaly_type == 2:
                record["tax"] = -tax
            else:
                record["total"] = None
        records.append(record)
    return records


def _value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


def canonical_to_invoice(raw: str) -> Dict[str, Any]:
    data = json.loads(raw) if isinstance(raw, str) else raw
    totals = data.get("totals", {})
    dates = data.get("dates", {})
    seller = data.get("seller", {})
    buyer = data.get("buyer", {})
    line_items = data.get("line_items", [])
    tax_rate = data.get("_meta", {}).get("vat_rate")
    if tax_rate is None and line_items:
        tax_rate = _value(line_items[0].get("tax_rate"))
    return {
        "invoice_number": _value(data.get("invoice_number")),
        "date": _value(dates.get("issue")),
        "due_date": _value(dates.get("due")),
        "vendor": _value(seller.get("name")),
        "vendor_address": _value(seller.get("address")),
        "vendor_tax_id": _value(seller.get("tax_id")),
        "client": _value(buyer.get("name")),
        "subtotal": _value(totals.get("subtotal")),
        "tax_rate": tax_rate,
        "tax": _value(totals.get("tax_total")),
        "total": _value(totals.get("grand_total")),
    }


def parquet_records(path: Path) -> List[Dict[str, Any]]:
    frame = pd.read_parquet(path, columns=["sample_id", "canonical"])
    records = []
    for row in frame.to_dict("records"):
        record = canonical_to_invoice(row["canonical"])
        record["sample_id"] = row["sample_id"]
        records.append(record)
    return records


def load_records(source: Path) -> Tuple[List[Dict[str, Any]], str]:
    if source.is_file() and source.suffix.lower() == ".parquet":
        return parquet_records(source), f"{source.name} canonical records"
    parquet_train = source / "train.parquet" if source.is_dir() else None
    if parquet_train and parquet_train.exists():
        return parquet_records(parquet_train), "InvoiceJSON train.parquet canonical records"
    paths = sorted(source.rglob("*.json")) if source.exists() else []
    records: List[Dict[str, Any]] = []
    for path in paths:
        try:
            records.extend(load_json_records(path))
        except (OSError, json.JSONDecodeError):
            continue
    if records:
        return records, "local JSON"
    return demo_records(), "deterministic demo invoices"


def corrupt_records(records: List[Dict[str, Any]], seed: int = 42) -> Tuple[List[Dict[str, Any]], List[int]]:
    rng = np.random.default_rng(seed)
    corrupted = []
    labels = []
    for index, original in enumerate(records):
        record = copy.deepcopy(original)
        if index % 5 == 0:
            anomaly_type = index % 4
            if anomaly_type == 0:
                record["vendor"] = None
            elif anomaly_type == 1:
                record["total"] = round(float(record.get("total") or 0) + rng.uniform(20, 400), 2)
            elif anomaly_type == 2:
                record["tax"] = -abs(float(record.get("tax") or 0))
            else:
                record["total"] = None
            labels.append(1)
        else:
            labels.append(0)
        corrupted.append(record)
    return corrupted, labels


def prepare_frame(records: List[Dict[str, Any]], labels: List[int] | None = None) -> Tuple[pd.DataFrame, pd.Series]:
    frame = pd.DataFrame(records)
    required = ["invoice_number", "date", "vendor", "subtotal", "tax", "total"]
    for column in required:
        if column not in frame:
            frame[column] = None
    frame = create_features(frame)
    if labels is None:
        frame = label_anomalies(frame)
        labels = frame["anomaly"].astype(int).tolist()
    X = frame.reindex(columns=FEATURE_COLUMNS, fill_value=0).astype(float).fillna(0)
    y = pd.Series(labels, index=frame.index, dtype=int)
    return X, y


def evaluate(model: Any, X_test: pd.DataFrame, y_test: pd.Series, name: str) -> Dict[str, Any]:
    prediction = np.asarray(model.predict(X_test)).astype(int)
    if set(prediction) == {-1, 1}:
        prediction = (prediction == -1).astype(int)
    row: Dict[str, Any] = {"model": name, "accuracy": accuracy_score(y_test, prediction), "precision": precision_score(y_test, prediction, zero_division=0), "recall": recall_score(y_test, prediction, zero_division=0), "f1": f1_score(y_test, prediction, zero_division=0)}
    if hasattr(model, "predict_proba"):
        row["roc_auc"] = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    else:
        row["roc_auc"] = np.nan
    return row


def train_models(source: str | Path = "data/raw/invoicejson/json", output_dir: str | Path = "models") -> pd.DataFrame:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    source_path = Path(source)
    records, source_name = load_records(source_path)
    training_records, training_labels = corrupt_records(records)
    X, y = prepare_frame(training_records, training_labels)
    if y.nunique() < 2:
        raise ValueError("Training data must contain both normal and anomalous invoices.")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, stratify=y, random_state=42)

    models = {
        "logistic_regression": Pipeline([("scaler", StandardScaler()), ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))]),
        "random_forest": RandomForestClassifier(n_estimators=250, class_weight="balanced", random_state=42, n_jobs=-1),
    }
    rows: List[Dict[str, Any]] = []
    for name, model in models.items():
        model.fit(X_train, y_train)
        joblib.dump(model, output / f"{name}.pkl")
        row = evaluate(model, X_test, y_test, name)
        row["split"] = "train_holdout"
        row["data_source"] = source_name
        rows.append(row)

    isolation = IsolationForest(n_estimators=250, contamination=float(y.mean()), random_state=42)
    isolation.fit(X_train[y_train == 0])
    joblib.dump(isolation, output / "isolation_forest.pkl")
    rows.append({**evaluate(isolation, X_test, y_test, "isolation_forest"), "split": "train_holdout", "data_source": source_name})

    if source_path.is_dir():
        for split in ("validation", "test"):
            split_path = source_path / f"{split}.parquet"
            if not split_path.exists():
                continue
            split_records = parquet_records(split_path)
            corrupted_split, split_labels = corrupt_records(split_records, seed=43 if split == "validation" else 44)
            X_split, y_split = prepare_frame(corrupted_split, split_labels)
            for name, model in [("logistic_regression", models["logistic_regression"]), ("random_forest", models["random_forest"]), ("isolation_forest", isolation)]:
                row = evaluate(model, X_split, y_split, name)
                row["split"] = split
                row["data_source"] = f"InvoiceJSON {split}.parquet canonical records"
                rows.append(row)

    (output / "feature_config.json").write_text(json.dumps({"feature_columns": FEATURE_COLUMNS, "data_source": source_name, "records": len(records)}, indent=2), encoding="utf-8")
    report = pd.DataFrame(rows)
    report.to_csv(ROOT / "outputs" / "reports" / "model_comparison.csv", index=False)
    print(f"Trained {len(models) + 1} models on {len(records)} real invoices from {source_name}; anomaly labels were generated by controlled corruption.")
    print(report.to_string(index=False))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Train invoice anomaly models.")
    parser.add_argument("--source", default="data/raw/invoicejson/json")
    parser.add_argument("--output-dir", default="models")
    args = parser.parse_args()
    train_models(args.source, args.output_dir)


if __name__ == "__main__":
    main()
