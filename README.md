# OCR_Text_Extractor

Interactive Gradio application for extracting text from PDFs and images using EasyOCR. Models are downloaded on first use and cached in `models/easyocr`.

## Quickstart
1. Create venv (optional): `python -m venv .venv`
2. Activate: `.\.venv\Scripts\Activate.ps1`
3. Install deps: `pip install -r requirements.txt`
4. Run app: `python src\OCR_App\main.py`
5. Tests (if added): `pytest -q`

## Usage
- Drop one or more PDF/image files into the uploader.
- Choose additional OCR languages if needed (defaults to English only).
- Extracted text appears in the textbox; multiple files are separated with headings.

Model weights download the first time each language is used and remain cached for reuse.
