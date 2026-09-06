# AI Invoice Anomaly Detector

Automated Invoice Preprocessing, Validation & ML-Based Anomaly Detection.

## Overview
This project processes invoice images and invoice JSON files, extracts normalized fields, validates them with rule-based logic, and scores them with machine learning models.

## Problem Statement
Invoice data often arrives in inconsistent formats. Missing fields, OCR errors, and mismatched totals can create downstream accounting and compliance issues. This project demonstrates a practical internship-level workflow for detecting those issues.

## Objectives
- Accept invoice images and JSON files
- Extract and normalize invoice fields
- Validate totals and required fields
- Detect anomalies with rules and ML
- Generate a risk score and explanation
- Present results in a Streamlit dashboard

## Important Limitation
The supervised labels in this project are rule-derived. High ML metrics on this dataset do not mean real-world fraud detection accuracy.

## Tech Stack
Python, Pandas, NumPy, Scikit-learn, Joblib, Pillow, OpenCV, Pytesseract, Streamlit, Matplotlib, pytest

## Dataset
Uses `AmineTibari/InvoiceJSON` via the Hugging Face `datasets` package.

## Colab Setup
1. `pip install -r requirements.txt`
2. `python -m src.main --prepare-data`
3. `python -m src.main --train`
4. `pytest`
5. `streamlit run app.py`

For public sharing in Colab, start Streamlit locally after confirming `curl http://127.0.0.1:8501` works, then expose it using a tunnel service.

## Project Structure
See the repository tree in the prompt.

## React Frontend
The production-style React dashboard lives in `frontend/`. It opens on the Home page and includes Dashboard, Inventory, About, and Analyze flows. It uses mock data when `VITE_API_URL` is not configured, with a visible `Demo data` indicator.

```bash
cd frontend
npm install
npm run dev
```

To connect FastAPI, create `frontend/.env` with:

```bash
VITE_API_URL=http://127.0.0.1:8000
```

Start the invoice API from the project root in a second terminal:

```bash
python -m uvicorn backend:app --reload --port 8000
```

The API service expects `GET /api/invoices`, `GET /api/invoices/{invoice_number}`, `GET /api/statistics`, `GET /api/models/performance`, and `POST /api/analyze` with a multipart `file` field. The frontend keeps these calls in `frontend/src/api/`.

Successful analyzer results are persisted to `outputs/predictions/processed_invoices.json` and are the only invoices shown in the React Inventory page. Training data is not automatically loaded into Inventory.

## OCR Setup
The project includes a local Windows Tesseract runtime under `tools/tesseract/`. `src/ocr_engine.py` automatically checks this folder first, then the standard Windows installation paths, then `PATH`. Restart the backend after changing OCR files:

```bash
python -m uvicorn backend:app --reload --port 8000
```

## Running
Install dependencies and train the included demo model set:

```bash
pip install -r requirements.txt
python -m src.train
streamlit run app.py
```

If JSON invoices are available locally, place them under `data/raw/invoicejson/json` before training. The trainer automatically uses those records; when the folder is empty it uses deterministic demo invoices with injected validation anomalies so the complete dashboard is usable immediately.

For the supplied Parquet dataset, train directly from its split directory:

```bash
python -m src.train --source "Z:\invoice-anomaly-detection\data\Dataset_input"
```

This reads `train.parquet` for fitting and reports metrics for the provided `validation.parquet` and `test.parquet` splits. Because these files contain canonical invoice data rather than anomaly labels, the trainer creates transparent controlled-corruption labels for benchmarking.

The training command writes `models/logistic_regression.pkl`, `models/random_forest.pkl`, `models/isolation_forest.pkl`, `models/feature_config.json`, and `outputs/reports/model_comparison.csv`.

## Testing
Run `pytest`.

## Limitations
- OCR quality depends on image quality
- JSON schemas can still vary beyond the handled cases
- Rule-derived labels are not ground-truth fraud labels

## Future Improvements
- Better OCR post-processing
- Larger labeled dataset
- More model comparison options

## Author
Internship Project Template
