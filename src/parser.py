from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .preprocessing import clean_number


def amount_to_float(value: Any) -> Optional[float]:
    return clean_number(value)


def _search_keys(obj: Any, keys: set[str]) -> Any:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in keys:
                return v
        for v in obj.values():
            found = _search_keys(v, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _search_keys(item, keys)
            if found is not None:
                return found
    return None


def _canonical_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


def _parse_canonical(data: Dict[str, Any]) -> Dict[str, Any]:
    totals = data.get("totals", {})
    dates = data.get("dates", {})
    seller = data.get("seller", {})
    buyer = data.get("buyer", {})
    lines = data.get("line_items", [])
    tax_rate = data.get("_meta", {}).get("vat_rate")
    if tax_rate is None and lines:
        tax_rate = _canonical_value(lines[0].get("tax_rate"))
    return {
        "invoice_number": _canonical_value(data.get("invoice_number")),
        "date": _canonical_value(dates.get("issue")),
        "due_date": _canonical_value(dates.get("due")),
        "vendor": _canonical_value(seller.get("name")),
        "vendor_address": _canonical_value(seller.get("address")),
        "vendor_tax_id": _canonical_value(seller.get("tax_id")),
        "client": _canonical_value(buyer.get("name")),
        "subtotal": amount_to_float(_canonical_value(totals.get("subtotal"))),
        "tax_rate": amount_to_float(tax_rate),
        "tax": amount_to_float(_canonical_value(totals.get("tax_total"))),
        "total": amount_to_float(_canonical_value(totals.get("grand_total"))),
    }


def parse_invoice(json_path: str | Path) -> Dict[str, Any]:
    path = Path(json_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("totals"), dict) and isinstance(data.get("seller"), dict):
        return _parse_canonical(data)
    mapping = {
        "invoice_number": {"invoice_number", "invoicenumber", "invoice_no", "number"},
        "date": {"date", "invoice_date"},
        "due_date": {"due_date", "duedate"},
        "vendor": {"vendor", "supplier", "seller"},
        "vendor_address": {"vendor_address", "address"},
        "vendor_tax_id": {"vendor_tax_id", "tax_id", "vat"},
        "client": {"client", "customer", "buyer"},
        "subtotal": {"subtotal", "sub_total", "net_total", "amount_before_tax"},
        "tax_rate": {"tax_rate", "vat_rate"},
        "tax": {"tax", "vat_amount"},
        "total": {"total", "grand_total", "amount_due"},
    }
    result: Dict[str, Any] = {}
    for out_key, keys in mapping.items():
        val = _search_keys(data, keys)
        if out_key in {"subtotal", "tax_rate", "tax", "total"}:
            result[out_key] = amount_to_float(val)
        else:
            result[out_key] = val
    return result
