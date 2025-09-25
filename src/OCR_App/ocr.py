from __future__ import annotations

import io
import statistics
from pathlib import Path
from typing import Iterable, List, Sequence

import easyocr
import numpy as np
from PIL import Image

try:
    import fitz  # type: ignore
except ImportError as exc:  # pragma: no cover - handled by requirements
    raise RuntimeError("PyMuPDF (fitz) is required for PDF OCR support") from exc

_MODEL_ROOT = Path(__file__).resolve().parent.parent / "models" / "easyocr"
_MODEL_ROOT.mkdir(parents=True, exist_ok=True)

_SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
_DEFAULT_LANGUAGES = ["en"]
_reader: easyocr.Reader | None = None


def _ensure_reader(languages: Sequence[str] | None = None) -> easyocr.Reader:
    """Create or return a cached EasyOCR reader using the local models folder."""
    global _reader
    if _reader is not None:
        return _reader

    langs = list(languages) if languages else _DEFAULT_LANGUAGES
    _MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    _reader = easyocr.Reader(  # type: ignore[assignment]
        lang_list=langs,
        gpu=False,
        model_storage_directory=str(_MODEL_ROOT),
        user_network_directory=str(_MODEL_ROOT),
        download_enabled=True,
    )
    return _reader


def _group_by_line(results: Iterable[tuple], line_spacing: float) -> List[List[tuple]]:
    """Group OCR results into lines based on vertical proximity."""
    sorted_items = sorted(
        (
            (np.mean([pt[1] for pt in bbox]), np.mean([pt[0] for pt in bbox]), bbox, text)
            for bbox, text, _conf in results
            if isinstance(text, str) and text.strip()
        ),
        key=lambda item: (item[0], item[1]),
    )
    if not sorted_items:
        return []

    lines: List[List[tuple]] = [[sorted_items[0]]]
    for item in sorted_items[1:]:
        prev_line = lines[-1]
        if abs(item[0] - prev_line[-1][0]) <= line_spacing:
            prev_line.append(item)
        else:
            lines.append([item])
    return lines


def _format_results(results: List[tuple]) -> str:
    if not results:
        return ""

    heights = [max(pt[1] for pt in bbox) - min(pt[1] for pt in bbox) for bbox, *_ in results]
    typical_height = statistics.median(heights) if heights else 10.0
    line_spacing = max(typical_height * 0.6, 8.0)

    grouped_lines = _group_by_line(results, line_spacing=line_spacing)
    output_lines: List[str] = []
    for line in grouped_lines:
        line_sorted = sorted(line, key=lambda item: item[1])
        line_text = " ".join(segment[3].strip() for segment in line_sorted)
        output_lines.append(line_text)
    return "\n".join(output_lines)


def extract_text_from_image(image: Image.Image, languages: Sequence[str] | None = None) -> str:
    """Run OCR on a PIL image and return formatted text."""
    reader = _ensure_reader(languages)
    image_np = np.array(image.convert("RGB"))
    results = reader.readtext(image_np)
    return _format_results(results)


def extract_text_from_pdf(pdf_path: Path, languages: Sequence[str] | None = None) -> str:
    """Convert PDF pages to images and run OCR on each page."""
    texts: List[str] = []
    with fitz.open(pdf_path) as document:
        for page_index in range(len(document)):
            page = document[page_index]
            # upscale slightly to improve OCR accuracy while keeping performance reasonable
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            with Image.open(io.BytesIO(pix.tobytes("png"))) as img:
                texts.append(extract_text_from_image(img, languages=languages))
    return "\n\n".join(text for text in texts if text)


def extract_text_from_path(path: Path, languages: Sequence[str] | None = None) -> str:
    """Dispatch OCR based on file extension."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path, languages=languages)
    if suffix in _SUPPORTED_IMAGE_EXTENSIONS:
        with Image.open(path) as image:
            return extract_text_from_image(image, languages=languages)
    raise ValueError(f"Unsupported file type: {suffix}")


__all__ = [
    "extract_text_from_image",
    "extract_text_from_pdf",
    "extract_text_from_path",
]
