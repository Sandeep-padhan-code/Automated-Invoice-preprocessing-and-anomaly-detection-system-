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

    # Strip zero-width bidirectional and formatting unicode markers
    for ch in ["\u200e", "\u200f", "\u202a", "\u202b", "\u202c", "\u202d", "\u202e", "\ufeff", "\u200b", "\u200c", "\u200d", "\u00a0"]:
        text = text.replace(ch, " ")

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = normalize_digits(text)

    # Normalize special characters and punctuation
    text = text.replace("—", "-").replace("–", "-")
    text = text.replace("：", ":").replace("٪", "%")
    text = text.replace("№", "No.").replace("N°", "No.").replace("Nº", "No.")
    text = text.replace("€", " EUR ").replace("£", " GBP ").replace("$", " USD ")
    text = text.replace("₹", " INR ").replace("¥", " JPY ")

    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
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
            for g in match.groups():
                if g and g.strip():
                    return g.strip()
    return None


def _clean_text_value(
    value: Optional[str],
) -> Optional[str]:
    if not value:
        return None

    value = value.strip()
    value = re.sub(r"[\s:;.,\-]+$", "", value)
    value = re.sub(r"^[\s:;.,\-]+", "", value)
    if len(value) <= 1 and not value.isdigit():
        return None
    return value if value else None


def _extract_amount(
    patterns: list[str],
    text: str,
) -> Optional[float]:
    value = _match(patterns, text)
    if value is None:
        return None

    value = normalize_digits(value)
    return clean_number(value)


# =====================# =========================================================
# INVOICE NUMBER (Multilingual: 20 Languages + RTL)
# =========================================================

def _extract_invoice_number(
    text: str,
) -> Optional[str]:
    patterns = [
        # English
        r"\b(?:invoice\s*(?:number|no\.?|num\.?|#)|inv(?:oice)?\s*(?:number|no\.?|num\.?|#)|bill\s*(?:number|no\.?|num\.?|#))\s*[:.\-#]?\s*([A-Z0-9][A-Z0-9./_\-]*)",

        # Spanish
        r"\b(?:n[uú]mero\s*(?:de\s*)?factura|factura\s*(?:no\.?|n[º°o]?\.?|num\.?|#)|n[º°o]?\.?\s*factura)\s*[:.\-#]?\s*([A-Z0-9][A-Z0-9./_\-]*)",

        # French
        r"\b(?:num[eé]ro\s*(?:de\s*)?facture|facture\s*(?:no\.?|n[°ºo]?\.?|num\.?|#)|n[°ºo]?\.?\s*facture)\s*[:.\-#]?\s*([A-Z0-9][A-Z0-9./_\-]*)",

        # German
        r"\b(?:rechnungsnummer|rechnung\s*(?:nr\.?|no\.?|#)|rechnungs-nr\.?|belegnummer)\s*[:.\-#]?\s*([A-Z0-9][A-Z0-9./_\-]*)",

        # Italian
        r"\b(?:numero\s*fattura|fattura\s*(?:n[.°]?|num\.?|no\.?)|n\s*doc\.?)\s*[:.\-#]?\s*([A-Z0-9][A-Z0-9./_\-]*)",

        # Portuguese
        r"\b(?:n[uú]mero\s*(?:da\s*)?fatura|fatura\s*(?:no\.?|n[º°o]?\.?|num\.?|#))\s*[:.\-#]?\s*([A-Z0-9][A-Z0-9./_\-]*)",

        # Dutch
        r"\b(?:factuurnummer|factuur\s*(?:nr\.?|no\.?|#)|factuur-nr\.?)\s*[:.\-#]?\s*([A-Z0-9][A-Z0-9./_\-]*)",

        # Turkish
        r"\b(?:fatura\s*(?:no\.?|numaras[ıi]|seri\s*no))\s*[:.\-#]?\s*([A-Z0-9][A-Z0-9./_\-]*)",

        # Arabic / Urdu (LTR and RTL value-label order)
        r"(?:رقم\s*الفاتورة|رقم\s*فاتورة|الفاتورة\s*رقم|فاتورة\s*رقم|بل\s*نمبر|انوائس\s*نمبر)\s*[:\-#]?\s*([A-Z0-9./_\-]+)",
        r"([A-Z0-9./_\-]+)\s*(?:[^\n\r]*?)?\s*(?:فاتورة\s*رقم|رقم\s*الفاتورة|رقم\s*فاتورة)",

        # Hindi / Marathi
        r"(?:बिल\s*नंबर|बिल\s*क्रमांक|चालान\s*नंबर|चालान\s*क्रमांक|बीजक\s*संख्या|पावती\s*क्रमांक)\s*[:\-#]?\s*([A-Z0-9./_\-]+)",

        # Bengali
        r"(?:চালান\s*নম্বর|বিল\s*নম্বর|ইনভয়েস\s*নং)\s*[:\-#]?\s*([A-Z0-9./_\-]+)",

        # Tamil
        r"(?:விலைப்பட்டியல்\s*எண்|பில்\s*எண்)\s*[:\-#]?\s*([A-Z0-9./_\-]+)",

        # Telugu
        r"(?:ఇన్వాయిస్\s*సంఖ్య|బిల్లు\s*సంఖ్య)\s*[:\-#]?\s*([A-Z0-9./_\-]+)",

        # Kannada / Malayalam / Gujarati / Punjabi / Odia
        r"(?:ಇನ್ವಾಯ್ಸ್\s*ಸಂಖ್ಯೆ|ഇൻവോയ്സ്\s*നമ്പർ|ઈનવોઈસ\s*નંબર|ਇਨਵੌਇਸ\s*ਨੰਬਰ|ଇନଭଏସ\s*ନମ୍ବର)\s*[:\-]?\s*([A-Z0-9./_\-]+)",

        # Generic invoice prefix
        r"\b(?:INV|BILL|REC|FAC)[-_\s]?([0-9]{3,}[A-Z0-9./_\-]*)",
        r"\b(?:invoice|factura|facture|rechnung|fattura|fatura)\s*[:.\-#]?\s*([A-Z0-9]{2,}[-/]?[A-Z0-9./_\-]+)",
    ]

    value = _match(patterns, text)
    return _clean_text_value(value)


# =========================================================
# VENDOR (Multilingual: 20 Languages)
# =========================================================

def _extract_vendor(
    text: str,
) -> Optional[str]:
    patterns = [
        # English
        r"^\s*(?:vendor|supplier|seller|company|merchant|from|billed\s+by|issued\s+by)\s*[:.\-]\s*(.+)$",

        # Spanish
        r"^\s*(?:proveedor|vendedor|emisor|empresa|expedido\s+por)\s*[:.\-]\s*(.+)$",

        # French
        r"^\s*(?:vendeur|fournisseur|[eé]metteur|soci[eé]t[eé]|entreprise)\s*[:.\-]\s*(.+)$",

        # German
        r"^\s*(?:lieferant|verk[aä]ufer|aussteller|firma|unternehmen)\s*[:.\-]\s*(.+)$",

        # Italian
        r"^\s*(?:fornitore|cedente|venditore|emittente|ditta)\s*[:.\-]\s*(.+)$",

        # Portuguese
        r"^\s*(?:fornecedor|vendedor|emitente|empresa)\s*[:.\-]\s*(.+)$",

        # Dutch
        r"^\s*(?:leverancier|verkoper|afzender|bedrijf)\s*[:.\-]\s*(.+)$",

        # Turkish
        r"^\s*(?:sat[ıi]c[ıi]|tedarik[çc]i|hizmet\s+veren|firma)\s*[:.\-]\s*(.+)$",

        # Arabic / Urdu
        r"(?:الجهة\s*البائعة|البائع|المورد|اسم\s*البائع|اسم\s*المورد|فروشندہ|سپلائر)\s*[:.\-]?\s*([^\n\r]+)",
        r"(?:مجموعة\s+[^\n\r]+)",

        # Hindi / Marathi
        r"^\s*(?:विक्रेता|आपूर्तिकर्ता|कंपनी|दुकान|सेवा\s*प्रदाता)\s*[:.\-]\s*(.+)$",

        # Indic
        r"^\s*(?:বিক্রেতা|விற்பனையாளர்|విక్రేత|ಮಾರಾಟಗಾರ|വിൽപ്പനക്കാരൻ|વિક્રેતા|ਵਿਕਰੇਤਾ|ବିକ୍ରେତା)\s*[:.\-]\s*(.+)$",

        # Flexible fallback
        r"\b(?:vendor|supplier|proveedor|vendeur|lieferant|fornitore|fornecedor|leverancier)\s*[:.\-]\s*([^\n\r]+)",
    ]

    value = _match(patterns, text)
    return _clean_text_value(value)


# =========================================================
# DATE (Multilingual: 20 Languages + RTL)
# =========================================================

def _extract_date(
    text: str,
) -> Optional[str]:
    date_value = r"([0-9]{1,4}[./\-][0-9]{1,2}[./\-][0-9]{1,4})"

    patterns = [
        # English
        rf"\b(?:invoice\s+date|issue\s+date|billing\s+date|date)\s*[:.\-]?\s*{date_value}",

        # Spanish
        rf"(?:fecha\s*de\s*factura|fecha\s*de\s*emisi[oó]n|fecha\s*emisi[oó]n|fecha)\s*[:.\-]?\s*{date_value}",

        # French
        rf"(?:date\s*de\s*facture|date\s*d['’]?[eé]mission|date\s*facture|date)\s*[:.\-]?\s*{date_value}",

        # German
        rf"(?:rechnungsdatum|ausstellungsdatum|belegdatum|datum)\s*[:.\-]?\s*{date_value}",

        # Italian / Portuguese / Dutch / Turkish
        rf"(?:data\s*fattura|data\s*emissione|data\s*documento|data\s*da\s*fatura|data\s*de\s*emiss[aã]o|factuurdatum|fatura\s*tarihi|d[uü]zenleme\s*tarihi|data|datum|tarih)\s*[:.\-]?\s*{date_value}",

        # Arabic / Urdu (LTR and RTL)
        rf"(?:تاريخ\s*الإصدار|تاريخ\s*الفاتورة|تاريخ|تاریخ\s*بل|تاریخ)\s*[:.\-]?\s*{date_value}",
        rf"{date_value}\s*[:.\-]?\s*(?:تاريخ\s*الإصدار|تاريخ\s*الفاتورة|تاريخ|تاریخ\s*بل|تاریخ)",

        # Indic
        rf"(?:चालान\s*तिथि|बिल\s*तिथि|दिनांक|तारीख|চালান\s*তারিখ|তারিখ|தேதி|తేదీ|ದಿನಾಂಕ|തീയതി|તારીખ|ਮਿਤੀ|ତାରିଖ)\s*[:.\-]?\s*{date_value}",
    ]

    return _clean_text_value(_match(patterns, text))


# =========================================================
# DUE DATE (Multilingual: 20 Languages + RTL)
# =========================================================

def _extract_due_date(
    text: str,
) -> Optional[str]:
    date_value = r"([0-9]{1,4}[./\-][0-9]{1,2}[./\-][0-9]{1,4})"

    patterns = [
        # English
        rf"\b(?:due\s+date|payment\s+due|pay\s+by|expiry\s+date)\s*[:.\-]?\s*{date_value}",

        # Spanish
        rf"(?:fecha\s*de\s*vencimiento|vencimiento|fecha\s*l[ií]mite)\s*[:.\-]?\s*{date_value}",

        # French
        rf"(?:date\s*d['’]?[eé]ch[eé]ance|[eé]ch[eé]ance|[aà]\s*payer\s*avant\s*le)\s*[:.\-]?\s*{date_value}",

        # German
        rf"(?:zahlungsziel|f[aä]lligkeitsdatum|f[aä]llig\s*am|zahlbar\s*bis)\s*[:.\-]?\s*{date_value}",

        # Italian / Portuguese / Dutch / Turkish
        rf"(?:data\s*scadenza|scadenza|data\s*de\s*vencimento|vencimento|vervaldatum|vade\s*tarihi|son\s*[oö]deme\s*tarihi)\s*[:.\-]?\s*{date_value}",

        # Arabic / Urdu (LTR and RTL)
        rf"(?:تاريخ\s*الاستحقاق|موعد\s*الاستحقاق|الاستحقاق|آخری\s*تاریخ)\s*[:.\-]?\s*{date_value}",
        rf"{date_value}\s*[:.\-]?\s*(?:تاريخ\s*الاستحقاق|موعد\s*الاستحقاق|الاستحقاق|آخری\s*تاریخ)",

        # Indic
        rf"(?:नियत\s*तिथि|भुगतान\s*तिथि|देय\s*तिथि|পরিশোধের\s*তারিখ|கெடு\s*தேதி|గడువు\s*తేదీ)\s*[:.\-]?\s*{date_value}",
    ]

    return _clean_text_value(_match(patterns, text))


# =========================================================
# AMOUNT REGEX HELPERS
# =========================================================

CURRENCY_PREFIX = r"(?:[$€£¥₹]|USD|EUR|GBP|JPY|INR|SAR|AED|DH|LE|TL|Rs\.?|ر\.س|جنيه)?\s*"
AMOUNT_PATTERN = (
    rf"{CURRENCY_PREFIX}"
    r"[\d.,\s]+"
    r"(?:\s*(?:[$€£¥₹]|USD|EUR|GBP|JPY|INR|SAR|AED|DH|LE|TL|Rs\.?|ر\.س|جنيه))?"
)


# =========================================================
# SUBTOTAL (Multilingual: 20 Languages + RTL)
# =========================================================

def _extract_subtotal(
    text: str,
) -> Optional[float]:
    patterns = [
        # English
        rf"\b(?:sub\s*total|subtotal|net\s*amount|amount\s*before\s*tax|total\s*net)\s*[:.\-]?\s*({AMOUNT_PATTERN})",

        # Spanish
        rf"(?:base\s*imponible|subtotal|importe\s*neto|total\s*neto)\s*[:.\-]?\s*({AMOUNT_PATTERN})",

        # French
        rf"(?:sous-total|sous\s*total|total\s*ht|montant\s*ht|net\s*ht)\s*[:.\-]?\s*({AMOUNT_PATTERN})",

        # German
        rf"(?:nettobetrag|zwischensumme|gesamt\s*netto|netto|summe\s*netto)\s*[:.\-]?\s*({AMOUNT_PATTERN})",

        # Italian
        rf"(?:imponibile|subtotale|totale\s*imponibile|totale\s*netto)\s*[:.\-]?\s*({AMOUNT_PATTERN})",

        # Portuguese
        rf"(?:subtotal|base\s*de\s*incid[eê]ncia|valor\s*l[ií]quido|total\s*il[ií]quido)\s*[:.\-]?\s*({AMOUNT_PATTERN})",

        # Dutch / Turkish
        rf"(?:subtotaal|excl\s*btw|totaal\s*excl\s*btw|netto\s*bedrag|ara\s*toplam|matrah|kdv\s*hari[çc]\s*toplam|net\s*tutar)\s*[:.\-]?\s*({AMOUNT_PATTERN})",

        # Arabic / Urdu (LTR and RTL)
        rf"(?:المجموع\s*الفرع[يئىه]|الإجمالي\s*الفرع[يئىه]|المبلغ\s*الصافي|جزوی\s*رقم|کل\s*رقم\s*قبل\s*از\s*ٹیکس)\s*[:.\-]?\s*({AMOUNT_PATTERN})",
        rf"({AMOUNT_PATTERN})\s*[:.\-]?\s*(?:المجموع\s*الفرع[يئىه]|الإجمالي\s*الفرع[يئىه]|المبلغ\s*الصافي)",

        # Indic
        rf"(?:उप\s*योग|उपयोग|कर\s*से\s*पहले\s*राशि|शुद्ध\s*राशि|একুণ\s*रक्कम|উপমোট|துணை\s*மொத்தம்|ఉప\s*మొత్తം)\s*[:.\-]?\s*({AMOUNT_PATTERN})",
    ]

    return _extract_amount(patterns, text)


# =========================================================
# TAX RATE (Multilingual: 20 Languages)
# =========================================================

def _extract_tax_rate(
    text: str,
) -> Optional[float]:
    patterns = [
        # English
        r"\b(?:tax\s*rate|vat\s*rate|gst\s*rate|sales\s*tax\s*rate)\s*[:.\-]?\s*([\d.,]+)\s*%",
        r"\b(?:tax|vat|gst)\s*[:.\-]?\s*\(?([\d.,]+)\s*%\)?",

        # European
        r"(?:tipo\s*impositivo|tipo\s*de\s*iva|taux\s*tva|mwst-satz|steuersatz|aliquota\s*iva|taxa\s*de\s*iva|btw\s*percentage|kdv\s*oran[ıi])\s*[:.\-]?\s*\(?([\d.,]+)\s*%\)?",

        # Arabic / Urdu / Indic
        r"(?:نسبة\s*الضريبة|معدل\s*الضريبة|ضريبة|ٹیکس\s*شرح|कर\s*दर|जीएसटी\s*दर|কর\s*হার|ভ্যাট\s*হার)\s*[:.\-]?\s*\(?([\d.,]+)\s*%\)?",
    ]

    return _extract_amount(patterns, text)


# =========================================================
# TAX AMOUNT (Multilingual: 20 Languages + RTL)
# =========================================================

def _extract_tax(
    text: str,
) -> Optional[float]:
    patterns = [
        # English
        rf"^\s*(?:tax|vat|gst|sales\s+tax)\s*[:.\-]?\s*({AMOUNT_PATTERN})\s*$",
        rf"\b(?:tax\s+amount|vat\s+amount|gst\s+amount|sales\s+tax\s+amount)\s*[:.\-]?\s*({AMOUNT_PATTERN})",
        rf"\b(?:tax|vat|gst)\s*(?:\([\d.,]+%\))?\s*[:.\-]?\s*({AMOUNT_PATTERN})",

        # European (IVA, TVA, MwSt, BTW, KDV)
        rf"(?:cuota\s*iva|importe\s*iva|impuesto\s*iva|impuesto|iva)\s*(?:\([\d.,]+%\))?\s*[:.\-]?\s*({AMOUNT_PATTERN})",
        rf"(?:montant\s*tva|total\s*tva|taxe|tva)\s*(?:\([\d.,]+%\))?\s*[:.\-]?\s*({AMOUNT_PATTERN})",
        rf"(?:steuerbetrag|mehrwertsteuer|umsatzsteuer|mwst|ust)\s*(?:\([\d.,]+%\))?\s*[:.\-]?\s*({AMOUNT_PATTERN})",
        rf"(?:totale\s*iva|imposta\s*totale|imposta|valor\s*do\s*iva|btw\s*bedrag|totaal\s*btw|kdv\s*tutar[ıi]|hesaplanan\s*kdv)\s*(?:\([\d.,]+%\))?\s*[:.\-]?\s*({AMOUNT_PATTERN})",

        # Arabic / Urdu (LTR and RTL)
        rf"(?:إجمالي\s*الضريبة|قيمة\s*الضريبة|ضريبة\s*القيمة\s*المضافة|الضريبة|ٹیکس|جی\s*ایس\s*ٹی)\s*[:.\-]?\s*({AMOUNT_PATTERN})",
        rf"({AMOUNT_PATTERN})\s*[:.\-]?\s*(?:إجمالي\s*الضريبة|قيمة\s*الضريبة|ضريبة\s*القيمة\s*المضافة|الضريبة)",

        # Indic
        rf"(?:कर\s*राशि|जीएसटी|टैक्स|कर|কর\s*পরিমাণ|வரி\s*தொகை|పన్ను\s*మొత్తం)\s*[:.\-]?\s*({AMOUNT_PATTERN})",
    ]

    return _extract_amount(patterns, text)


# =========================================================
# TOTAL (Multilingual: 20 Languages + RTL)
# =========================================================

def _extract_total(
    text: str,
) -> Optional[float]:
    patterns = [
        # English
        rf"\b(?:grand\s+total|total\s+amount|amount\s+due|total\s+due|net\s+payable|total\s+payable|balance\s+due)\s*[:.\-]?\s*({AMOUNT_PATTERN})",
        rf"^\s*total\s*[:.\-]?\s*({AMOUNT_PATTERN})\s*$",

        # European
        rf"(?:total\s*factura|importe\s*total|total\s*a\s*pagar|total\s*general)\s*[:.\-]?\s*({AMOUNT_PATTERN})",
        rf"(?:total\s*ttc|montant\s*ttc|net\s*[aà]\s*payer|total\s*[aà]\s*payer|montant\s*total)\s*[:.\-]?\s*({AMOUNT_PATTERN})",
        rf"(?:gesamtbetrag|rechnungsbetrag|endbetrag|zu\s*zahlen|zahlbetrag|gesamt)\s*[:.\-]?\s*({AMOUNT_PATTERN})",
        rf"(?:totale\s*fattura|importo\s*totale|total\s*da\s*fatura|totaalbedrag|factuurbedrag|genel\s*toplam|[oö]denecek\s*tutar)\s*[:.\-]?\s*({AMOUNT_PATTERN})",

        # Arabic / Urdu (LTR and RTL)
        rf"(?:المبلغ\s*المستحق|الإجمالي\s*النهائي|الإجمالي|المجموع\s*الكلي|إجمالي\s*المبلغ|کل\s*رقم|ٹوٹل)\s*[:.\-]?\s*({AMOUNT_PATTERN})",
        rf"({AMOUNT_PATTERN})\s*[:.\-]?\s*(?:المبلغ\s*المستحق|الإجمالي\s*النهائي|الإجمالي|المجموع\s*الكلي|إجمالي\s*المبلغ)",

        # Indic
        rf"(?:कुल\s*राशि|कुल\s*योग|अंतिम\s*योग|देय\s*राशि|একूण\s*बेरीज|মোট\s*পরিমাণ|மொத்தம்|మొత్తం|ಒಟ್ಟು\s*ಮೊತ್ತ|ആകെ\s*തുക|કુલ\s*રકમ|ਕੁੱਲ\s*ਰਕਮ|ମୋଟ\s*ରାଶି)\s*[:.\-]?\s*({AMOUNT_PATTERN})",

        # Generic trailing total
        rf"\b(?:total|totale|totaal|toplam)\s*[:.\-]?\s*({AMOUNT_PATTERN})",
    ]

    return _extract_amount(patterns, text)


# =========================================================
# FALLBACK TOTAL
# =========================================================

def _fallback_total(
    text: str,
    subtotal: Optional[float],
    tax: Optional[float],
) -> Optional[float]:
    """
    If no total label was detected, attempt to find a likely final amount near the end.
    """
    if subtotal is None and tax is None:
        return None

    lines = text.splitlines()
    candidates = []

    amount_pattern = re.compile(
        r"(?<![\d])"
        r"(?:[$€£¥₹]|USD|EUR|GBP|INR|SAR|AED|DH|LE|TL|Rs\.?|ر\.س)?\s*"
        r"[\d,]+(?:\.\d{1,2})?"
        r"(?![\d])"
    )

    for line in lines[-8:]:
        matches = amount_pattern.findall(line)
        for value in matches:
            number = clean_number(normalize_digits(value))
            if number is not None:
                candidates.append(number)

    if not candidates:
        return None

    expected = (subtotal or 0) + (tax or 0)
    if expected <= 0:
        return candidates[-1] if candidates else None

    # Prefer a value closest to expected sum
    closest = min(candidates, key=lambda x: abs(x - expected))
    difference = abs(closest - expected)

    if difference <= max(1.0, expected * 0.10):
        return closest

    return None


# =========================================================
# MAIN PARSER
# =========================================================

def parse_ocr_text(
    text: str,
) -> Dict[str, Any]:
    """
    Convert OCR text into a standardized invoice dictionary across 20+ languages.
    """
    normalized = _normalize_text(text)

    if not normalized:
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

    invoice_number = _extract_invoice_number(normalized)
    vendor = _extract_vendor(normalized)
    date = _extract_date(normalized)
    due_date = _extract_due_date(normalized)
    subtotal = _extract_subtotal(normalized)
    tax_rate = _extract_tax_rate(normalized)
    tax = _extract_tax(normalized)
    total = _extract_total(normalized)

    # Conservative fallback
    if total is None:
        total = _fallback_total(normalized, subtotal, tax)

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
