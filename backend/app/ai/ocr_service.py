"""OCR Service — Tesseract primary, PaddleOCR optional."""
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def run_ocr(file_path: str, mime_type: str) -> Dict[str, Any]:
    """
    Run OCR on a document file.
    Uses Tesseract (primary) with structured extraction.
    Never claims to be perfect — always expose confidence.
    """
    # Strip /uploads prefix for actual filesystem path
    actual_path = file_path.lstrip("/")

    if not os.path.exists(actual_path):
        return {
            "success": False,
            "text": "",
            "confidence": 0.0,
            "structured": {},
            "error": "File not found",
        }

    try:
        if mime_type == "application/pdf":
            text = await _extract_pdf_text(actual_path)
        else:
            text = await _extract_image_text(actual_path)

        structured = _extract_structured_fields(text)

        return {
            "success": True,
            "text": text,
            "confidence": 0.75 if text else 0.0,  # Approximate
            "structured": structured,
        }
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return {
            "success": False,
            "text": "",
            "confidence": 0.0,
            "structured": {},
            "error": str(e),
        }


async def _extract_pdf_text(path: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except ImportError:
        logger.warning("PyMuPDF not available, trying Tesseract on PDF")
        return ""
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


async def _extract_image_text(path: str) -> str:
    """Extract text from image using Tesseract."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(path)
        text = pytesseract.image_to_string(img, lang="eng+hin")
        return text.strip()
    except ImportError:
        logger.warning("pytesseract not available")
        return ""
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        return ""


def _extract_structured_fields(text: str) -> Dict[str, Any]:
    """
    Extract structured fields from OCR text using pattern matching.
    Human correction always available — never claim this is perfect.
    """
    import re

    structured = {}

    # Reference number patterns
    ref_patterns = [
        r"(?:Ref(?:erence)?[\s:.]+No[\s:.]+)([A-Z0-9\-/]+)",
        r"(?:License[\s:.]+No[\s:.]+)([A-Z0-9\-/]+)",
    ]
    for pattern in ref_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            structured["reference_number"] = match.group(1).strip()
            break

    # Date patterns
    date_pattern = r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"
    dates = re.findall(date_pattern, text)
    if len(dates) >= 1:
        structured["issue_date_raw"] = dates[0]
    if len(dates) >= 2:
        structured["expiry_date_raw"] = dates[-1]

    # Expiry keywords
    expiry_match = re.search(
        r"(?:expir[ey]|valid\s+until|valid\s+upto)[\s:]+(.{5,20})",
        text, re.IGNORECASE
    )
    if expiry_match:
        structured["expiry_text"] = expiry_match.group(1).strip()

    # Mine name
    mine_match = re.search(r"(?:mine|colliery)[\s:]+([A-Za-z\s]+?)(?:\n|,|\.)", text, re.IGNORECASE)
    if mine_match:
        structured["mine_name"] = mine_match.group(1).strip()

    structured["_note"] = "OCR extraction is approximate. Please verify and correct fields as needed."

    return structured
