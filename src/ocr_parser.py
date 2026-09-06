from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .preprocessing import clean_number


# =========================================================
# DIGIT NORMALIZATION
# =========================================================

ARABIC_DIGITS = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩",
    "0123456789",
)

PERSIAN_DIGITS = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹",
    "0123456789",
)


def normalize_digits(value: str) -> str:
    """
    Convert Arabic/Persian numerals to normal ASCII digits.
    """

    if not value:
        return value

    value = value.translate(ARABIC_DIGITS)
    value = value.translate(PERSIAN_DIGITS)

    return value


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def _normalize_text(text: str) -> str:

    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = normalize_digits(text)

    # Normalize punctuation
    text = text.replace("—", "-")
    text = text.replace("–", "-")
    text = text.replace("：", ":")
    text = text.replace("٪", "%")

    lines = []

    for line in text.split("\n"):

        line = re.sub(
            r"[ \t]+",
            " ",
            line,
        ).strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


# =========================================================
# REGEX MATCH
# =========================================================

def _match(
    patterns: list[str],
    text: str,
) -> Optional[str]:

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.MULTILINE,
        )

        if match:

            value = match.group(1).strip()

            return value

    return None


def _clean_text_value(
    value: Optional[str],
) -> Optional[str]:

    if not value:
        return None

    value = value.strip()

    value = re.sub(
        r"[\s:;]+$",
        "",
        value,
    )

    return value if value else None


def _extract_amount(
    patterns: list[str],
    text: str,
) -> Optional[float]:

    value = _match(
        patterns,
        text,
    )

    if value is None:
        return None

    value = normalize_digits(value)

    return clean_number(value)


# =========================================================
# INVOICE NUMBER
# =========================================================

def _extract_invoice_number(
    text: str,
) -> Optional[str]:

    patterns = [

        # English
        r"\binvoice\s*(?:number|no|num|#)\s*[.:#\-]?\s*([A-Z0-9][A-Z0-9./_-]*)",

        r"\binv(?:oice)?\s*(?:number|no|num|#)\s*[.:#\-]?\s*([A-Z0-9][A-Z0-9./_-]*)",

        r"\bbill\s*(?:number|no|num|#)\s*[.:#\-]?\s*([A-Z0-9][A-Z0-9./_-]*)",

        # Arabic
        r"(?:رقم\s*الفاتورة|رقم\s*فاتورة|الفاتورة\s*رقم)\s*[:\-#]?\s*([A-Z0-9./_-]+)",

        # Hindi
        r"(?:बिल\s*नंबर|बिल\s*क्रमांक|चालान\s*नंबर)\s*[:\-#]?\s*([A-Z0-9./_-]+)",

        # Bengali
        r"(?:চালান\s*নম্বর|বিল\s*নম্বর)\s*[:\-#]?\s*([A-Z0-9./_-]+)",

        # Generic invoice pattern
        r"\binvoice\s*[#:]?\s*([A-Z]{0,5}[-/]?\d[A-Z0-9./_-]*)",
    ]

    value = _match(
        patterns,
        text,
    )

    return _clean_text_value(value)


# =========================================================
# VENDOR
# =========================================================

def _extract_vendor(
    text: str,
) -> Optional[str]:

    patterns = [

        # English
        r"^\s*(?:vendor|supplier|seller|company|merchant)\s*[:\-]\s*(.+)$",

        r"^\s*(?:from|billed\s+by|issued\s+by)\s*[:\-]\s*(.+)$",

        # Arabic
        r"^\s*(?:البائع|المورد|اسم\s*البائع|اسم\s*المورد)\s*[:\-]\s*(.+)$",

        # Hindi
        r"^\s*(?:विक्रेता|आपूर्तिकर्ता|कंपनी)\s*[:\-]\s*(.+)$",

        # Bengali
        r"^\s*(?:বিক্রেতা|সরবরাহকারী|কোম্পানি)\s*[:\-]\s*(.+)$",

        # Tamil
        r"^\s*(?:விற்பனையாளர்|சப்ளையர்|நிறுவனம்)\s*[:\-]\s*(.+)$",

        # Telugu
        r"^\s*(?:విక్రేత|సరఫరాదారు|కంపెనీ)\s*[:\-]\s*(.+)$",

        # Generic
        r"^\s*(?:vendor|supplier|seller)\s+(.+)$",
    ]

    value = _match(
        patterns,
        text,
    )

    return _clean_text_value(value)


# =========================================================
# DATE
# =========================================================

def _extract_date(
    text: str,
) -> Optional[str]:

    date_value = (
        r"([0-9]{1,4}[./-][0-9]{1,2}[./-][0-9]{1,4})"
    )

    patterns = [

        # English
        rf"\binvoice\s+date\s*[:\-]?\s*{date_value}",
        rf"\bissue\s+date\s*[:\-]?\s*{date_value}",
        rf"\bdate\s*[:\-]?\s*{date_value}",

        # Arabic
        rf"(?:تاريخ\s*الفاتورة|تاريخ\s*الإصدار|تاريخ)\s*[:\-]?\s*{date_value}",

        # Hindi
        rf"(?:चालान\s*तिथि|बिल\s*तिथि|दिनांक|तारीख)\s*[:\-]?\s*{date_value}",

        # Bengali
        rf"(?:চালান\s*তারিখ|বিল\s*তারিখ|তারিখ)\s*[:\-]?\s*{date_value}",

        # Tamil
        rf"(?:விலைப்பட்டியல்\s*தேதி|தேதி)\s*[:\-]?\s*{date_value}",

        # Telugu
        rf"(?:ఇన్వాయిస్\s*తేదీ|తేదీ)\s*[:\-]?\s*{date_value}",
    ]

    return _clean_text_value(
        _match(
            patterns,
            text,
        )
    )


# =========================================================
# DUE DATE
# =========================================================

def _extract_due_date(
    text: str,
) -> Optional[str]:

    date_value = (
        r"([0-9]{1,4}[./-][0-9]{1,2}[./-][0-9]{1,4})"
    )

    patterns = [

        # English
        rf"\bdue\s+date\s*[:\-]?\s*{date_value}",
        rf"\bpayment\s+due\s*[:\-]?\s*{date_value}",

        # Arabic
        rf"(?:تاريخ\s*الاستحقاق|تاريخ\s*الاستحقاق)\s*[:\-]?\s*{date_value}",

        # Hindi
        rf"(?:नियत\s*तिथि|भुगतान\s*तिथि|देय\s*तिथि)\s*[:\-]?\s*{date_value}",

        # Bengali
        rf"(?:পরিশোধের\s*তারিখ|প্রাপ্য\s*তারিখ)\s*[:\-]?\s*{date_value}",
    ]

    return _clean_text_value(
        _match(
            patterns,
            text,
        )
    )


# =========================================================
# SUBTOTAL
# =========================================================

def _extract_subtotal(
    text: str,
) -> Optional[float]:

    amount = (
        r"([$€£₹$€£]|ر\.س|SAR)?\s*"
        r"[\d,]+(?:\.\d{1,2})?"
    )

    patterns = [

        # English
        rf"\bsub\s*total\s*[:\-]?\s*({amount})",
        rf"\bsubtotal\s*[:\-]?\s*({amount})",
        rf"\bnet\s*amount\s*[:\-]?\s*({amount})",
        rf"\bamount\s*before\s*tax\s*[:\-]?\s*({amount})",

        # Arabic
        rf"(?:المجموع\s*الفرعي|الإجمالي\s*الفرعي|المبلغ\s*الصافي)\s*[:\-]?\s*({amount})",

        # Hindi
        rf"(?:उप\s*योग|उपयोग|कर\s*से\s*पहले\s*राशि|शुद्ध\s*राशि)\s*[:\-]?\s*({amount})",

        # Bengali
        rf"(?:উপমোট|কর\s*পূর্ব\s*মূল্য|নিট\s*পরিমাণ)\s*[:\-]?\s*({amount})",

        # Tamil
        rf"(?:துணை\s*மொத்தம்|நிகர\s*தொகை)\s*[:\-]?\s*({amount})",

        # Telugu
        rf"(?:ఉప\s*మొత్తం|నికర\s*మొత్తం)\s*[:\-]?\s*({amount})",
    ]

    return _extract_amount(
        patterns,
        text,
    )


# =========================================================
# TAX RATE
# =========================================================

def _extract_tax_rate(
    text: str,
) -> Optional[float]:

    patterns = [

        # English
        r"\btax\s+rate\s*[:\-]?\s*([\d.,]+)\s*%",
        r"\bvat\s+rate\s*[:\-]?\s*([\d.,]+)\s*%",
        r"\bgst\s+rate\s*[:\-]?\s*([\d.,]+)\s*%",
        r"\bgst\s*[:\-]?\s*([\d.,]+)\s*%",
        r"\bvat\s*[:\-]?\s*([\d.,]+)\s*%",

        # Arabic
        r"(?:نسبة\s*الضريبة|معدل\s*الضريبة|ضريبة)\s*[:\-]?\s*([\d.,]+)\s*%",

        # Hindi
        r"(?:कर\s*दर|जीएसटी\s*दर)\s*[:\-]?\s*([\d.,]+)\s*%",

        # Bengali
        r"(?:কর\s*হার|ভ্যাট\s*হার)\s*[:\-]?\s*([\d.,]+)\s*%",
    ]

    return _extract_amount(
        patterns,
        text,
    )


# =========================================================
# TAX AMOUNT
# =========================================================

def _extract_tax(
    text: str,
) -> Optional[float]:

    amount = (
        r"([$€£₹]|ر\.س|SAR)?\s*"
        r"[\d,]+(?:\.\d{1,2})?"
    )

    patterns = [

        # English
        rf"^\s*tax\s*[:\-]?\s*({amount})\s*$",
        rf"\btax\s+amount\s*[:\-]?\s*({amount})",
        rf"\bvat\s+amount\s*[:\-]?\s*({amount})",
        rf"\bgst\s+amount\s*[:\-]?\s*({amount})",
        rf"^\s*vat\s*[:\-]?\s*({amount})\s*$",
        rf"^\s*gst\s*[:\-]?\s*({amount})\s*$",

        # Arabic
        rf"(?:قيمة\s*الضريبة|ضريبة\s*القيمة\s*المضافة|الضريبة)\s*[:\-]?\s*({amount})",

        # Hindi
        rf"(?:कर\s*राशि|जीएसटी|टैक्स)\s*[:\-]?\s*({amount})",

        # Bengali
        rf"(?:কর\s*পরিমাণ|ভ্যাট|জিএসটি)\s*[:\-]?\s*({amount})",
    ]

    return _extract_amount(
        patterns,
        text,
    )


# =========================================================
# TOTAL
# =========================================================

def _extract_total(
    text: str,
) -> Optional[float]:

    amount = (
        r"([$€£₹]|ر\.س|SAR)?\s*"
        r"[\d,]+(?:\.\d{1,2})?"
    )

    patterns = [

        # English
        rf"\bgrand\s+total\s*[:\-]?\s*({amount})",
        rf"\btotal\s+amount\s*[:\-]?\s*({amount})",
        rf"\bamount\s+due\s*[:\-]?\s*({amount})",
        rf"\btotal\s+due\s*[:\-]?\s*({amount})",
        rf"\bnet\s+payable\s*[:\-]?\s*({amount})",
        rf"\btotal\s+payable\s*[:\-]?\s*({amount})",
        rf"^\s*total\s*[:\-]?\s*({amount})\s*$",

        # Arabic
        rf"(?:الإجمالي\s*النهائي|الإجمالي|المجموع\s*الكلي|المبلغ\s*المستحق|إجمالي\s*المبلغ)\s*[:\-]?\s*({amount})",

        # Hindi
        rf"(?:कुल\s*राशि|कुल\s*योग|अंतिम\s*योग|देय\s*राशि)\s*[:\-]?\s*({amount})",

        # Bengali
        rf"(?:মোট\s*পরিমাণ|সর্বমোট|মোট)\s*[:\-]?\s*({amount})",

        # Tamil
        rf"(?:மொத்தம்|மொத்த\s*தொகை|இறுதி\s*மொத்தம்)\s*[:\-]?\s*({amount})",

        # Telugu
        rf"(?:మొత్తం|మొత్తం\s*మొత్తము|చెల్లించాల్సిన\s*మొత్తం)\s*[:\-]?\s*({amount})",
    ]

    return _extract_amount(
        patterns,
        text,
    )


# =========================================================
# FALLBACK TOTAL
# =========================================================

def _fallback_total(
    text: str,
    subtotal: Optional[float],
    tax: Optional[float],
) -> Optional[float]:
    """
    If no total label was detected, attempt to find a
    likely final amount near the end of the invoice.

    This is deliberately conservative.
    """

    if subtotal is None and tax is None:
        return None

    lines = text.splitlines()

    candidates = []

    amount_pattern = re.compile(
        r"(?<![\d])"
        r"(?:[$€£₹]|ر\.س|SAR)?\s*"
        r"[\d,]+(?:\.\d{1,2})?"
        r"(?![\d])"
    )

    for line in lines[-8:]:

        matches = amount_pattern.findall(line)

        for value in matches:

            number = clean_number(
                normalize_digits(value)
            )

            if number is not None:
                candidates.append(number)

    if not candidates:
        return None

    expected = (
        (subtotal or 0)
        + (tax or 0)
    )

    # Prefer a value close to subtotal + tax
    closest = min(
        candidates,
        key=lambda x: abs(x - expected),
    )

    if expected > 0:

        difference = abs(
            closest - expected
        )

        if difference <= max(
            1.0,
            expected * 0.10,
        ):
            return closest

    return None


# =========================================================
# MAIN PARSER
# =========================================================

def parse_ocr_text(
    text: str,
) -> Dict[str, Any]:
    """
    Convert OCR text into a standardized invoice dictionary.

    Output fields are language-independent.
    """

    text = _normalize_text(text)

    if not text:

        return {
            "invoice_number": None,
            "vendor": None,
            "date": None,
            "due_date": None,
            "subtotal": None,
            "tax_rate": None,
            "tax": None,
            "total": None,
        }

    invoice_number = _extract_invoice_number(text)

    vendor = _extract_vendor(text)

    date = _extract_date(text)

    due_date = _extract_due_date(text)

    subtotal = _extract_subtotal(text)

    tax_rate = _extract_tax_rate(text)

    tax = _extract_tax(text)

    total = _extract_total(text)

    # Conservative fallback
    if total is None:

        total = _fallback_total(
            text,
            subtotal,
            tax,
        )

    return {
        "invoice_number": invoice_number,
        "vendor": vendor,
        "date": date,
        "due_date": due_date,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax": tax,
        "total": total,
    }

