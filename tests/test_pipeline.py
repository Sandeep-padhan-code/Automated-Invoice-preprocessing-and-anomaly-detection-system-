from src.main import InvoicePipeline


def test_pipeline_normal():
    pipe = InvoicePipeline(model_path="models/missing.pkl")
    out = pipe.process_invoice({"invoice_number": "1", "date": "2024-01-01", "vendor": "A", "subtotal": 100, "tax": 10, "total": 110})
    assert out["final_decision"] == "NORMAL"

