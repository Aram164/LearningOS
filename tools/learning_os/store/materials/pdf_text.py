"""PDF extraction from immutable observed bytes, shared by slices and anchors."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pypdf import PdfReader


class PDFTextError(ValueError):
    """A dependency, parser, encryption, page or extraction failure."""


def pdf_reader(content: bytes) -> PdfReader:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PDFTextError("pypdf is required: make setup") from exc
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            raise PDFTextError("encrypted PDF requires an explicitly readable material")
        return reader
    except PDFTextError:
        raise
    except Exception as exc:
        raise PDFTextError(f"file cannot be parsed as PDF: {exc}") from exc


def pdf_page_text(reader: PdfReader, page: int) -> str:
    try:
        if type(page) is not int or not 1 <= page <= len(reader.pages):
            raise PDFTextError(f"PDF page {page} is outside this {len(reader.pages)}-page file")
        text = reader.pages[page - 1].extract_text()
    except PDFTextError:
        raise
    except Exception as exc:
        raise PDFTextError(f"PDF page {page} extraction failed: {exc}") from exc
    if text is None:
        return ""
    return text
