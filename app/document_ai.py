"""Document intelligence for PRITHVI.

Handles:
- PDF validation
- SHA-256 hashing
- text extraction with pypdf
- OCR fallback for scanned PDFs
- extraction of mine-inspection numeric readings

The module does not make fraud decisions. It only produces document-level
facts that the verification engine can turn into signals.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Optional


DOCUMENT_ROOT = (
    Path(__file__).resolve().parent / "data" / "documents"
)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hash of a file."""

    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(chunk)

    return h.hexdigest()


def validate_pdf(path: Path) -> None:
    """Validate that a document exists and is a PDF."""

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            "Document reference is not a file."
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF documents are supported."
        )


def _extract_pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))

    parts: list[str] = []

    for page in reader.pages:
        parts.append(
            page.extract_text() or ""
        )

    return "\n".join(parts).strip()


def _ocr_pdf(path: Path) -> str:
    import io

    import fitz
    import pytesseract
    from PIL import Image

    doc = fitz.open(str(path))

    pages: list[str] = []

    try:
        for page in doc:
            pix = page.get_pixmap(
                matrix=fitz.Matrix(1.8, 1.8),
                alpha=False,
            )

            image = Image.open(
                io.BytesIO(
                    pix.tobytes("png")
                )
            )

            pages.append(
                pytesseract.image_to_string(
                    image,
                    config="--psm 6",
                )
            )

    finally:
        doc.close()

    return "\n".join(pages).strip()


def extract_pdf_text(
    path: Path,
) -> tuple[str, str]:
    """Return (text, extraction_method).

    Text PDFs use pypdf.
    Image/scanned PDFs fall back to Tesseract OCR.
    """

    validate_pdf(path)

    text = _extract_pdf_text(path)

    if len(
        re.sub(r"\s+", "", text)
    ) >= 40:
        return text, "pdf_text"

    try:
        ocr_text = _ocr_pdf(path)

        if ocr_text:
            return (
                ocr_text,
                "tesseract_ocr",
            )

    except Exception as exc:

        if text:
            return (
                text,
                f"pdf_text_ocr_failed:{type(exc).__name__}",
            )

        raise

    return text, "pdf_text_empty"


def extract_numeric_readings(
    text: str,
) -> dict[str, Optional[float]]:
    """Best-effort extraction of mine-inspection measurements.

    Supports common wording variations such as:

        Methane concentration: 1.25%
        Methane concentration was 1.25%
        Methane concentration was recorded at 1.25%
        CH4 level = 1.25%

        Air quantity: 450 m3/min
        Air quantity was measured at 450 m3/min
        Airflow reading was 450 m3/min

        Temperature: 32 C
        Temperature was recorded at 32 C
        Temperature reading was 32 degrees Celsius
    """

    normalized = (
        text.lower()
        .replace(",", "")
        .replace("mÂ³", "m3")
        .replace("°", " ")
    )

    # Normalize common Unicode/wording variations.
    normalized = re.sub(
        r"\bpercent\b",
        "%",
        normalized,
    )

    normalized = re.sub(
        r"\bdegrees?\s+celsius\b",
        "c",
        normalized,
    )

    normalized = re.sub(
        r"\bdeg(?:rees?)?\.?\s*c\b",
        "c",
        normalized,
    )

    def first(
        patterns: list[str],
    ) -> Optional[float]:

        for pattern in patterns:

            match = re.search(
                pattern,
                normalized,
                flags=re.I,
            )

            if match:

                try:
                    return float(
                        match.group(1)
                    )

                except ValueError:
                    pass

        return None

    return {
        # ----------------------------------------------------
        # METHANE
        # ----------------------------------------------------

                "methane_pct": first(
            [
                r"\bmethane"
                r"(?:\s+concentration|\s+level|\s+reading)?"
                r"[\s\S]{0,60}?"
                r"(\d+(?:\.\d+)?)"
                r"\s*%",

                r"\bch4"
                r"(?:\s+concentration|\s+level|\s+reading)?"
                r"[\s\S]{0,60}?"
                r"(\d+(?:\.\d+)?)"
                r"\s*%",
            ]
        ),
# ----------------------------------------------------
# AIRFLOW
# ----------------------------------------------------

"airflow_m3_min": first(
    [
        r"\b(?:air\s+quantity|air\s+volume)\b[\s\S]{0,60}?"
        r"(\d+(?:\.\d+)?)\s*m3\s*/?\s*(?:min|minute)\b",

        r"\bairflow\b[\s\S]{0,60}?"
        r"(\d+(?:\.\d+)?)\s*m3\s*/?\s*(?:min|minute)\b",

        r"\bair\s+flow\b[\s\S]{0,60}?"
        r"(\d+(?:\.\d+)?)\s*m3\s*/?\s*(?:min|minute)\b",
    ]
),        # ----------------------------------------------------
        # TEMPERATURE
        # ----------------------------------------------------

               "temperature_c": first(
            [
                r"\btemperature"
                r"(?:\s+(?:reading|value|measurement))?"
                r"[\s\S]{0,60}?"
                r"(-?\d+(?:\.\d+)?)"
                r"\s*c\b",

                r"\btemp"
                r"(?:\s+(?:reading|value|measurement))?"
                r"[\s\S]{0,60}?"
                r"(-?\d+(?:\.\d+)?)"
                r"\s*c\b",
            ]
        ),
    }

def resolve_document_reference(
    storage_reference: str,
) -> Path:
    """Resolve a stored document reference safely.

    Relative references are resolved inside DOCUMENT_ROOT.
    Absolute references are allowed only when they point inside
    DOCUMENT_ROOT.

    This prevents arbitrary filesystem access through a database
    storage_reference value.
    """

    if not storage_reference:
        raise ValueError(
            "Document storage reference is empty."
        )

    reference = Path(storage_reference)

    if reference.is_absolute():
        candidate = reference.resolve()
    else:
        candidate = (
            DOCUMENT_ROOT / reference
        ).resolve()

    root = DOCUMENT_ROOT.resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            "Document reference points outside "
            "the PRITHVI document store."
        ) from exc

    return candidate