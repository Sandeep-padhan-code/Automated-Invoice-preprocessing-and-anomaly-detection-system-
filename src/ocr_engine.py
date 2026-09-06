from __future__ import annotations

from pathlib import Path
from typing import Optional
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
    Find Tesseract installation.
    """

    project_binary = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "tesseract"
        / "tesseract.exe"
    )

    candidates = [
        project_binary,
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]

    for candidate in candidates:

        if candidate.exists():

            pytesseract.pytesseract.tesseract_cmd = str(candidate)

            return candidate

    discovered = shutil.which("tesseract")

    if discovered:

        pytesseract.pytesseract.tesseract_cmd = discovered

        return Path(discovered)

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
    language: str = "auto"
) -> str:

    language = language.lower().strip()

    # Explicit language
    if language in LANGUAGES:
        return LANGUAGES[language]

    # Direct Tesseract language code
    if language in LANGUAGES.values():
        return language

    # Automatic mode
    if language == "auto":

        installed = set(get_installed_languages())

        # Prefer a broad multilingual configuration
        preferred = [
            "eng",
            "ara",
            "hin",
            "ben",
            "ori",
            "tam",
            "tel",
            "kan",
            "mal",
            "mar",
            "guj",
            "pan",
            "urd",
            "fra",
            "deu",
            "spa",
            "por",
            "ita",
            "nld",
            "tur",
        ]

        available = [
            code
            for code in preferred
            if code in installed
        ]

        if available:
            return "+".join(available)

        return "eng"

    return "eng"


# =========================================================
# IMAGE PREPROCESSING
# =========================================================

def preprocess_for_ocr(image: Image.Image) -> np.ndarray:
    """
    Prepare invoice image for OCR.
    """

    image = ImageOps.exif_transpose(image)

    image = image.convert("RGB")

    gray = ImageOps.grayscale(image)

    arr = np.array(gray)

    # Upscale
    arr = cv2.resize(
        arr,
        None,
        fx=2.0,
        fy=2.0,
        interpolation=cv2.INTER_CUBIC,
    )

    # Remove small noise
    arr = cv2.GaussianBlur(
        arr,
        (3, 3),
        0,
    )

    # Adaptive threshold works better for uneven invoice lighting
    binary = cv2.adaptiveThreshold(
        arr,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    return binary


# =========================================================
# OCR
# =========================================================

def extract_text(
    image_path: str | Path,
    language: str = "auto",
) -> str:
    """
    Extract text from an invoice image.

    Parameters
    ----------
    image_path:
        Path to invoice image.

    language:
        Language name such as:
            english
            arabic
            hindi
            bengali
            odia
            tamil
            telugu
            kannada
            malayalam
            marathi
            gujarati
            punjabi
            urdu
            french
            german
            spanish
            portuguese
            italian
            dutch
            turkish

        Use 'auto' for automatic multilingual mode.
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

        # Resolve OCR language
        lang = resolve_language(language)

        # Tesseract configuration
        config = "--oem 3 --psm 6"

        # OCR
        text = pytesseract.image_to_string(
            processed,
            lang=lang,
            config=config,
        )

        text = text.strip()

        if not text:
            return (
                "OCR_ERROR: Tesseract returned no text. "
                "Try a clearer image or check that the required "
                "language data is installed."
            )

        return text

    except pytesseract.TesseractError as exc:

        return (
            f"OCR_ERROR: Tesseract language/configuration error: {exc}"
        )

    except Exception as exc:

        return f"OCR_ERROR: {exc}"


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

