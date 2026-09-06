from pathlib import Path
import json

from src.parser import parse_invoice, amount_to_float


def test_amount_to_float():
    assert amount_to_float("$ 481,62") == 481.62


def test_parse_invoice(tmp_path: Path):
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"invoice_number": "A1", "vendor": "V", "total": "$10"}), encoding="utf-8")
    out = parse_invoice(p)
    assert out["invoice_number"] == "A1"

