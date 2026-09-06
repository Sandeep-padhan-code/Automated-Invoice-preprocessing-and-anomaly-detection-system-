from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from src.main import InvoicePipeline


st.set_page_config(page_title="LedgerLens | Invoice intelligence", page_icon="L", layout="wide", initial_sidebar_state="expanded")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');
        :root { --ink:#EAF4F1; --muted:#91AAA8; --paper:#071113; --panel:#0D1D20; --line:#1C3A3B; --teal:#41E0C0; --mint:#163E3D; --coral:#FF8067; }
        .stApp { background:radial-gradient(circle at 82% 4%, rgba(31,112,101,.2), transparent 25rem), radial-gradient(circle at 5% 90%, rgba(24,74,97,.18), transparent 23rem), var(--paper); color:var(--ink); }
        .stApp, .stApp p, .stApp label, [data-testid="stMetricLabel"] { font-family:'Manrope', sans-serif; }
        h1,h2,h3 { font-family:'Playfair Display', serif !important; color:var(--ink); letter-spacing:-.03em; }
        h1 { font-size:3.1rem !important; line-height:1.05 !important; margin-bottom:.45rem !important; }
        [data-testid="stSidebar"] { background:linear-gradient(180deg,#0A191B,#071113); border-right:1px solid var(--line); }
        [data-testid="stSidebar"] .block-container { padding:2rem 1.25rem; }
        .brand { display:flex; gap:10px; align-items:center; margin-bottom:2.3rem; }
        .brand-mark { width:37px; height:37px; display:grid; place-items:center; background:var(--teal); color:#061311; border-radius:12px; font-size:18px; font-weight:800; box-shadow:0 0 22px rgba(65,224,192,.55), 5px 5px 0 #164A47; }
        .brand-name { font-weight:800; font-size:1.1rem; letter-spacing:-.03em; }
        .brand-sub { color:var(--muted); font-size:.68rem; letter-spacing:.1em; text-transform:uppercase; }
        .eyebrow, .section-label { color:var(--teal); font-family:'DM Mono', monospace; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; }
        .eyebrow { margin-bottom:.9rem; }
        .section-label { margin:1.4rem 0 .65rem; color:var(--muted); font-size:.68rem; }
        .lede { color:var(--muted); font-size:1rem; max-width:690px; line-height:1.7; }
        .hero { padding:1.25rem 0 1.8rem; position:relative; }
        .hero:after { content:''; position:absolute; width:210px; height:210px; right:4%; top:-45px; border-radius:50%; background:radial-gradient(circle, rgba(65,224,192,.18) 0 42%, transparent 43%); box-shadow:0 0 90px rgba(65,224,192,.22); opacity:.9; z-index:0; }
        .hero > * { position:relative; z-index:1; }
        .card { background:linear-gradient(145deg, rgba(16,39,41,.96), rgba(9,25,28,.96)); border:1px solid var(--line); border-radius:18px; padding:1.15rem 1.2rem; box-shadow:0 10px 30px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.03); height:100%; }
        .card-title { font-weight:800; color:var(--ink); margin-bottom:.4rem; }
        .card-copy { color:var(--muted); font-size:.84rem; line-height:1.5; }
        .decision { border-radius:20px; padding:1.25rem 1.35rem; color:white; min-height:140px; position:relative; overflow:hidden; }
        .decision:after { content:''; position:absolute; width:140px; height:140px; border:1px solid rgba(255,255,255,.25); border-radius:50%; right:-35px; top:-45px; }
        .decision.normal { background:linear-gradient(135deg,#116B65,#0D4F51); box-shadow:0 0 34px rgba(65,224,192,.18); }
        .decision.anomaly { background:linear-gradient(135deg,#C65F43,#8E3D36); box-shadow:0 0 34px rgba(255,128,103,.18); }
        .decision-label { font-family:'DM Mono', monospace; font-size:.65rem; letter-spacing:.14em; opacity:.8; text-transform:uppercase; }
        .decision-value { font-family:'Playfair Display', serif; font-size:2.2rem; margin:.3rem 0; }
        .decision-note { opacity:.82; font-size:.78rem; }
        .finding { border-left:3px solid var(--coral); background:rgba(92,38,35,.28); padding:.75rem .85rem; border-radius:0 10px 10px 0; margin:.45rem 0; color:#FFC1B4; font-size:.83rem; }
        .finding.good { border-left-color:var(--teal); background:rgba(18,99,86,.22); color:#9BF1DD; }
        .mono { font-family:'DM Mono', monospace; }
        div[data-testid="stMetric"] { background:rgba(13,29,32,.9); border:1px solid var(--line); border-radius:15px; padding:.8rem 1rem; box-shadow:0 0 20px rgba(65,224,192,.05); }
        .stButton > button, .stDownloadButton > button { border-radius:11px; font-weight:700; border:1px solid #2B5956; min-height:2.65rem; background:#102628; color:var(--ink); }
        .stButton > button[kind="primary"] { background:var(--teal); border-color:var(--teal); }
        .stTabs [data-baseweb="tab-list"] { gap:1.4rem; border-bottom:1px solid var(--line); }
        .stTabs [data-baseweb="tab"] { font-weight:700; color:var(--muted); padding-left:0; padding-right:0; }
        .stTabs [aria-selected="true"] { color:var(--teal); }
        [data-testid="stFileUploader"] { background:rgba(13,29,32,.86); border:1px dashed #397C71; border-radius:18px; padding:.3rem; box-shadow:0 0 25px rgba(65,224,192,.06); }
        .sidebar-note { color:var(--muted); font-size:.75rem; line-height:1.6; padding-top:1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def json_safe(value: Any) -> Any:
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def analyze_file(uploaded_file: Any, pipeline: InvoicePipeline) -> Dict[str, Any]:
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix.lower())
    handle.write(uploaded_file.getvalue())
    handle.close()
    path = Path(handle.name)
    result = pipeline.process_json(path) if path.suffix == ".json" else pipeline.process_image(path)
    result["source_name"] = uploaded_file.name
    return result


def render_finding(text: str, good: bool = False) -> None:
    css = "finding good" if good else "finding"
    st.markdown(f'<div class="{css}">{"✓" if good else "!"}&nbsp;&nbsp;{text}</div>', unsafe_allow_html=True)


def render_decision(result: Dict[str, Any]) -> None:
    is_anomaly = result.get("final_decision") == "ANOMALY"
    note = "Review the highlighted evidence before approval." if is_anomaly else "No consistency issues detected by the current checks."
    state = "anomaly" if is_anomaly else "normal"
    label = "Needs review" if is_anomaly else "Looks consistent"
    st.markdown(f'<div class="decision {state}"><div class="decision-label">Final assessment</div><div class="decision-value">{label}</div><div class="decision-note">{note}</div></div>', unsafe_allow_html=True)


def render_summary(result: Dict[str, Any]) -> None:
    render_decision(result)
    st.markdown('<div class="section-label">Signal overview</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Risk score", f'{result.get("anomaly_score", 0)}/100')
    c2.metric("Severity", result.get("severity", "Unknown"))
    probability = result.get("ml_probability")
    c3.metric("ML probability", f"{probability:.0%}" if probability is not None else "Not loaded")
    c4.metric("Rule findings", len(result.get("rule_anomalies", [])))


def render_invoice_details(result: Dict[str, Any]) -> None:
    st.markdown('<div class="section-label">Extracted invoice</div>', unsafe_allow_html=True)
    left, right = st.columns([1.1, .9])
    fields = [("Invoice number", result.get("invoice_number")), ("Vendor", result.get("vendor")), ("Invoice date", result.get("date")), ("Due date", result.get("due_date")), ("Client", result.get("client")), ("Tax ID", result.get("vendor_tax_id"))]
    with left:
        for label, value in fields:
            shown = value if value not in (None, "") else "Not found"
            st.markdown(f'<div class="card" style="height:auto;margin-bottom:.55rem"><div class="section-label" style="margin:0 0 .2rem">{label}</div><div class="card-title">{shown}</div></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Financial consistency</div><div class="card-copy">The arithmetic check compares extracted values, with a tolerance of 0.05.</div>', unsafe_allow_html=True)
        subtotal, tax, total = result.get("subtotal"), result.get("tax"), result.get("total")
        expected = (subtotal or 0) + (tax or 0) if subtotal is not None or tax is not None else None
        financial = pd.DataFrame({"Amount": [subtotal or 0, tax or 0, total or 0], "Label": ["Subtotal", "Tax", "Total"]}).set_index("Label")
        st.bar_chart(financial, color="#0F766E", height=190)
        if expected is not None and total is not None:
            delta = total - expected
            tone = "#E36B4D" if abs(delta) > .05 else "#0F766E"
            st.markdown(f'<div class="mono" style="font-size:.78rem;color:{tone}">Expected total: {expected:,.2f} &nbsp; | &nbsp; Difference: {delta:,.2f}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_analysis(result: Dict[str, Any]) -> None:
    st.markdown('<div class="section-label">Why this decision?</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="card"><div class="card-title">Rule-based findings</div><div class="card-copy">Transparent checks that can be acted on immediately.</div>', unsafe_allow_html=True)
        findings = result.get("rule_anomalies", [])
        if findings:
            for finding in findings:
                render_finding(finding)
        else:
            render_finding("All required fields and totals are consistent.", good=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="card"><div class="card-title">Machine learning signal</div><div class="card-copy">The saved model is an additional signal, not a replacement for review.</div>', unsafe_allow_html=True)
        if result.get("ml_probability") is None:
            render_finding("No trained model found. Rule-based validation is active.", good=True)
        else:
            prediction = "Anomaly pattern" if result.get("ml_prediction") else "Normal pattern"
            render_finding(f'{prediction} with {result["ml_probability"]:.0%} estimated probability.', good=not bool(result.get("ml_prediction")))
        st.markdown('</div>', unsafe_allow_html=True)


def render_single(pipeline: InvoicePipeline) -> None:
    st.markdown('<div class="section-label">Single invoice</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Drop an invoice image or JSON file", type=["png", "jpg", "jpeg", "webp", "json"], key="single")
    if not uploaded:
        st.markdown('<div class="card" style="margin-top:1rem"><div class="card-title">Start with one invoice</div><div class="card-copy">LedgerLens extracts the key fields, checks the totals, and explains every risk signal in one reviewable report.</div></div>', unsafe_allow_html=True)
        if st.button("Load demo invoice", use_container_width=True):
            st.session_state["result"] = pipeline.process_invoice({"invoice_number": "LL-DEMO-1042", "date": "2024-08-19", "due_date": "2024-09-18", "vendor": "Northstar Office Supply", "vendor_tax_id": "IN-29-8842", "client": "LedgerLens Operations", "subtotal": 1480.00, "tax_rate": 18.0, "tax": 266.40, "total": 1746.40, "source_name": "demo_invoice.json"})
        if "result" not in st.session_state:
            return
    if st.button("Analyze invoice", type="primary", use_container_width=True):
        with st.spinner("Reading invoice and assembling evidence..."):
            try:
                st.session_state["result"] = analyze_file(uploaded, pipeline)
            except Exception as exc:
                st.error(f"Unable to analyze this file: {exc}")
    result = st.session_state.get("result")
    if result and (not uploaded or result.get("source_name") == uploaded.name):
        st.divider()
        if result.get("analysis_status") == "UNABLE_TO_ANALYZE":
            st.warning(result.get("analysis_message", "We could not analyze this invoice."))
        render_summary(result)
        review, raw = st.tabs(["Review", "Raw evidence"])
        with review:
            render_invoice_details(result)
            render_analysis(result)
            st.download_button("Download JSON report", json.dumps(json_safe(result), indent=2, ensure_ascii=True), file_name="invoice_review.json", mime="application/json", use_container_width=True)
        with raw:
            if result.get("ocr_text"):
                st.text_area("OCR text", result["ocr_text"], height=250)
            else:
                st.json(json_safe(result))


def render_batch(pipeline: InvoicePipeline) -> None:
    st.markdown('<div class="section-label">Batch review</div>', unsafe_allow_html=True)
    uploads = st.file_uploader("Upload multiple invoice files", type=["png", "jpg", "jpeg", "webp", "json"], accept_multiple_files=True, key="batch")
    if not uploads:
        st.markdown('<div class="card" style="margin-top:1rem"><div class="card-title">Review a queue at once</div><div class="card-copy">Upload a mixed set of JSON and image invoices to compare decisions, severity, and rule findings side by side.</div></div>', unsafe_allow_html=True)
        return
    if st.button("Run batch review", type="primary", use_container_width=True):
        rows: List[Dict[str, Any]] = []
        progress = st.progress(0, text="Preparing review queue...")
        for index, uploaded in enumerate(uploads):
            try:
                result = analyze_file(uploaded, pipeline)
                rows.append({"File": uploaded.name, "Decision": result.get("final_decision"), "Severity": result.get("severity"), "Risk score": result.get("anomaly_score", 0), "Findings": len(result.get("rule_anomalies", []))})
            except Exception as exc:
                rows.append({"File": uploaded.name, "Decision": "ERROR", "Severity": "Unknown", "Risk score": 0, "Findings": str(exc)})
            progress.progress((index + 1) / len(uploads), text=f"Reviewed {index + 1} of {len(uploads)}")
        st.session_state["batch_results"] = rows
    rows = st.session_state.get("batch_results", [])
    if rows:
        frame = pd.DataFrame(rows)
        st.divider()
        a, b, c = st.columns(3)
        a.metric("Invoices reviewed", len(frame))
        b.metric("Needs review", int((frame["Decision"] == "ANOMALY").sum()))
        c.metric("Average risk", f'{frame["Risk score"].mean():.0f}/100')
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.download_button("Download batch CSV", frame.to_csv(index=False), "batch_review.csv", "text/csv", use_container_width=True)


def main() -> None:
    inject_styles()
    with st.sidebar:
        st.markdown('<div class="brand"><div class="brand-mark">L</div><div><div class="brand-name">LedgerLens</div><div class="brand-sub">Invoice intelligence</div></div></div>', unsafe_allow_html=True)
        st.markdown("### Workspace")
        mode = st.radio("Choose a review mode", ["Single invoice", "Batch review"], label_visibility="collapsed")
        st.divider()
        model_path = st.selectbox("Decision model", ["models/logistic_regression.pkl", "models/random_forest.pkl", "models/isolation_forest.pkl"])
        st.markdown('<div class="sidebar-note">Rule checks are always active. A trained model is used automatically when the selected artifact exists in the models folder.</div>', unsafe_allow_html=True)
    pipeline = InvoicePipeline(model_path=model_path)
    st.markdown('<div class="hero"><div class="eyebrow">Accounts payable / signal desk</div><h1>Find the invoices<br>that need a second look.</h1><p class="lede">A focused review workspace for turning messy invoice files into clear, explainable decisions.</p></div>', unsafe_allow_html=True)
    if mode == "Single invoice":
        render_single(pipeline)
    else:
        render_batch(pipeline)
    st.markdown('<div style="text-align:center;color:#8A9796;font-size:.7rem;margin:3rem 0 1rem;font-family:DM Mono,monospace;letter-spacing:.08em">LEDGERLENS / REVIEW WITH CONFIDENCE</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
