from __future__ import annotations

from pathlib import Path
from typing import Optional
import os
import shutil
import re

import cv2
import numpy as np
from PIL import Image, ImageOps
import pytesseract


# =========================================================
# SUPPORTED LANGUAGES
# =========================================================

LANGUAGES = {
    "english": "eng",
    "arabic": "ara",
    "hindi": "hin",
    "bengali": "ben",
    "odia": "ori",
    "tamil": "tam",
    "telugu": "tel",
    "kannada": "kan",
    "malayalam": "mal",
    "marathi": "mar",
    "gujarati": "guj",
    "punjabi": "pan",
    "urdu": "urd",
    "french": "fra",
    "german": "deu",
    "spanish": "spa",
    "portuguese": "por",
    "italian": "ita",
    "dutch": "nld",
    "turkish": "tur",
}


# =========================================================
# SCRIPT DETECTION
# =========================================================

def detect_script(text: str) -> Optional[str]:
    """
    Detect the dominant writing system from OCR/sample text.

    This is useful when language='auto'.

    Note:
    Some languages share the same script. For example:
        French, German, Spanish, Italian, Dutch, Portuguese
    all use Latin script.

    Therefore script detection can identify the script,
    but cannot always identify the exact language.
    """

    if not text:
        return None

    counts = {
        "arabic": 0,
        "devanagari": 0,
        "bengali": 0,
        "odia": 0,
        "tamil": 0,
        "telugu": 0,
        "kannada": 0,
        "malayalam": 0,
        "gurmukhi": 0,
        "gujarati": 0,
        "latin": 0,
    }

    for char in text:

        code = ord(char)

        # Arabic / Urdu
        if (
            0x0600 <= code <= 0x06FF
            or 0x0750 <= code <= 0x077F
            or 0x08A0 <= code <= 0x08FF
        ):
            counts["arabic"] += 1

        # Devanagari
        elif 0x0900 <= code <= 0x097F:
            counts["devanagari"] += 1

        # Bengali
        elif 0x0980 <= code <= 0x09FF:
            counts["bengali"] += 1

        # Odia
        elif 0x0B00 <= code <= 0x0B7F:
            counts["odia"] += 1

        # Tamil
        elif 0x0B80 <= code <= 0x0BFF:
            counts["tamil"] += 1

        # Telugu
        elif 0x0C00 <= code <= 0x0C7F:
            counts["telugu"] += 1

        # Kannada
        elif 0x0C80 <= code <= 0x0CFF:
            counts["kannada"] += 1

        # Malayalam
        elif 0x0D00 <= code <= 0x0D7F:
            counts["malayalam"] += 1

        # Gujarati
        elif 0x0A80 <= code <= 0x0AFF:
            counts["gujarati"] += 1

        # Gurmukhi / Punjabi
        elif 0x0A00 <= code <= 0x0A7F:
            counts["gurmukhi"] += 1

        # Basic Latin
        elif (
            0x0041 <= code <= 0x005A
            or 0x0061 <= code <= 0x007A
        ):
            counts["latin"] += 1

    detected = max(counts, key=counts.get)

    if counts[detected] == 0:
        return None

    return detected


# =========================================================
# MAP SCRIPT → TESSERACT LANGUAGE
# =========================================================

SCRIPT_TO_LANGUAGE = {
    "arabic": "ara+eng",
    "devanagari": "hin+eng",
    "bengali": "ben+eng",
    "odia": "ori+eng",
    "tamil": "tam+eng",
    "telugu": "tel+eng",
    "kannada": "kan+eng",
    "malayalam": "mal+eng",
    "gujarati": "guj+eng",
    "gurmukhi": "pan+eng",
    "latin": "eng+fra+deu+spa+por+ita+nld+tur",
}


# =========================================================
# TESSERACT CONFIGURATION
# =========================================================

def configure_tesseract() -> Optional[Path]:
    """
    Find Tesseract installation on Windows or Linux and ensure
    tessdata directory containing all 20+ languages is loaded.
    """
    project_binary = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "tesseract"
        / "tesseract.exe"
    )
    project_tessdata = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "tesseract"
        / "tessdata"
    )

    # If project-bundled tessdata exists, ensure TESSDATA_PREFIX is set
    if project_tessdata.exists() and "TESSDATA_PREFIX" not in os.environ:
        os.environ["TESSDATA_PREFIX"] = str(project_tessdata)

    # Windows / project binary preferred if available with full language pack
    if project_binary.exists():
        pytesseract.pytesseract.tesseract_cmd = str(project_binary)
        return project_binary

    # Linux / Render / system-installed Tesseract
    discovered = shutil.which("tesseract")
    if discovered:
        pytesseract.pytesseract.tesseract_cmd = discovered
        return Path(discovered)

    candidates = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]

    for candidate in candidates:
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return candidate

    return None


TESSERACT_BINARY = configure_tesseract()


# =========================================================
# CHECK INSTALLED LANGUAGES
# =========================================================

def get_installed_languages() -> list[str]:
    """
    Return language codes installed in Tesseract.
    """

    if TESSERACT_BINARY is None:
        return []

    try:
        languages = pytesseract.get_languages(config="")
        return languages

    except Exception:
        return []


def get_supported_installed_languages() -> dict[str, str]:
    """
    Return only the configured languages that are actually
    installed in Tesseract.
    """

    installed = set(get_installed_languages())

    return {
        name: code
        for name, code in LANGUAGES.items()
        if code in installed
    }


# =========================================================
# LANGUAGE SELECTION
# =========================================================

def resolve_language(
    language: str = "auto",
    sample_text: Optional[str] = None,
) -> str:
    language = language.lower().strip()

    # Explicit language name
    if language in LANGUAGES:
        return LANGUAGES[language]

    # Direct Tesseract language code
    if language in LANGUAGES.values():
        return language

    # Automatic script detection if sample text is provided
    if language == "auto" and sample_text:
        script = detect_script(sample_text)
        if script and script in SCRIPT_TO_LANGUAGE:
            installed = set(get_installed_languages())
            target_langs = [l for l in SCRIPT_TO_LANGUAGE[script].split("+") if l in installed]
            if target_langs:
                return "+".join(target_langs)

    # Automatic mode default: Multi-script pack with Arabic, Hindi, and European languages
    if language == "auto":
        installed = set(get_installed_languages())
        auto_pack = ["ara", "hin", "eng", "fra", "deu", "spa", "por", "ita", "nld", "tur"]
        available = [code for code in auto_pack if code in installed]
        if available:
            return "+".join(available)
        return "eng" if "eng" in installed else ("+".join(list(installed)[:4]) if installed else "eng")

    return "eng"


# =========================================================
# IMAGE PREPROCESSING
# =========================================================

def preprocess_for_ocr(image: Image.Image) -> np.ndarray:
    """
    Prepare invoice image for OCR with dimension guards and contrast optimization.
    Preserves text edges without destructive binarization.
    """
    # Guard against decompression bombs and excessively huge images
    width, height = image.size
    if width > 10000 or height > 10000 or (width * height) > 30_000_000:
        raise ValueError(f"Image dimensions ({width}x{height}) exceed maximum allowed size.")

    # Auto-orient based on EXIF
    image = ImageOps.exif_transpose(image)
    gray = image.convert("L")
    arr = np.array(gray)

    # Upscale only if resolution is low (< 1400px max dimension)
    h, w = arr.shape
    if max(h, w) < 1400:
        arr = cv2.resize(
            arr,
            None,
            fx=2.0,
            fy=2.0,
            interpolation=cv2.INTER_CUBIC,
        )
    elif max(h, w) > 3000:
        scale = 2500.0 / max(h, w)
        arr = cv2.resize(
            arr,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA,
        )

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) for uneven illumination
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(arr)

    return enhanced


# =========================================================
# OCR
# =========================================================

def extract_text(
    image_path: str | Path,
    language: str = "auto",
) -> str:
    """
    Extract text from an invoice image across 20+ supported languages.
    """
    path = Path(image_path)

    if not path.exists():
        return f"OCR_ERROR: Image not found: {path}"

    if TESSERACT_BINARY is None:
        return (
            "OCR_ERROR: Tesseract was not found. "
            "Install Tesseract OCR and make sure the executable "
            "is available."
        )

    try:
        # Open image
        image = Image.open(path)

        # Preprocess
        processed = preprocess_for_ocr(image)

        # Tesseract configuration
        config = "--oem 3 --psm 6"

        if language == "auto":
            # Initial fast pass with Latin pack
            lang = resolve_language("auto")
            text = pytesseract.image_to_string(
                processed,
                lang=lang,
                config=config,
                timeout=25,
            ).strip()

            # Check if text contains non-Latin scripts (e.g. Arabic, Devanagari, Bengali, etc.)
            script = detect_script(text)
            if script and script != "latin":
                script_lang = resolve_language("auto", sample_text=text)
                if script_lang != lang:
                    re_text = pytesseract.image_to_string(
                        processed,
                        lang=script_lang,
                        config=config,
                        timeout=25,
                    ).strip()
                    if re_text:
                        text = re_text
        else:
            lang = resolve_language(language)
            text = pytesseract.image_to_string(
                processed,
                lang=lang,
                config=config,
                timeout=30,
            ).strip()

        if not text:
            return (
                "OCR_ERROR: Tesseract returned no text. "
                "Try a clearer image or check that the required "
                "language data is installed."
            )

        return text

    except getattr(pytesseract, "TesseractTimeoutError", RuntimeError) as exc:
        return "OCR_ERROR: OCR processing timed out after 30 seconds."

    except (Image.DecompressionBombError, ValueError) as exc:
        return f"OCR_ERROR: Invalid image file: {exc}"

    except pytesseract.TesseractError as exc:
        return f"OCR_ERROR: Tesseract language/configuration error: {exc}"

    except Exception as exc:
        return f"OCR_ERROR: Unexpected OCR error occurred: {exc}"


# =========================================================
# LANGUAGE-SPECIFIC OCR
# =========================================================

def extract_text_with_language(
    image_path: str | Path,
    language: str,
) -> str:
    """
    Convenience function for explicitly selecting a language.
    """

    return extract_text(
        image_path,
        language=language,
    )


# =========================================================
# OCR DIAGNOSTICS
# =========================================================

def ocr_status() -> dict:
    """
    Return OCR installation and language information.
    """

    installed = get_installed_languages()

    supported = get_supported_installed_languages()

    return {
        "tesseract_installed": TESSERACT_BINARY is not None,
        "tesseract_path": (
            str(TESSERACT_BINARY)
            if TESSERACT_BINARY
            else None
        ),
        "installed_languages": installed,
        "supported_languages_installed": supported,
        "supported_language_count": len(supported),
    }

