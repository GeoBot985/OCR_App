from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

import gradio as gr

from OCR_App.ocr import extract_text_from_path

_SUPPORTED_FILE_TYPES = [
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tiff",
    ".tif",
]


def _normalize_languages(languages):
    if not languages:
        return []
    normalized = set()
    for lang in languages:
        for token in str(lang).split(","):
            cleaned = token.strip().lower()
            if cleaned:
                normalized.add(cleaned)
    return sorted(normalized)


def _resolve_file_paths(files):
    if not files:
        return []

    if isinstance(files, (str, Path)):
        return [Path(files)]

    resolved = []
    sequence = files if isinstance(files, (list, tuple)) else [files]
    for item in sequence:
        if isinstance(item, (str, Path)):
            resolved.append(Path(item))
            continue
        if isinstance(item, dict):
            name = item.get("name") or item.get("path")
        else:
            name = getattr(item, "name", None) or getattr(item, "path", None)
        if name:
            resolved.append(Path(name))
    return resolved


def run_ocr_on_files(files, languages):
    file_paths = _resolve_file_paths(files)
    if not file_paths:
        return ""

    requested_languages = _normalize_languages(languages)
    languages_arg = requested_languages or None

    outputs = []
    for path in file_paths:
        if not path.exists():
            outputs.append(f"[warning] File not found: {path.name}")
            continue
        try:
            text = extract_text_from_path(path, languages=languages_arg)
        except Exception as exc:  # pylint: disable=broad-except
            outputs.append(f"[error] Failed to process {path.name}: {exc}")
            continue

        if len(file_paths) > 1:
            header = f"# {path.name}\n"
            outputs.append(header + (text or "(No text detected)"))
        else:
            outputs.append(text or "(No text detected)")

    return "\n\n".join(outputs)


def build_interface() -> gr.Interface:
    file_input = gr.File(
        label="Drop PDFs or images",
        file_count="multiple",
    )
    language_select = gr.CheckboxGroup(
        label="Languages",
        choices=["en", "es", "fr", "de", "it", "pt", "zh_sim", "ja"],
        value=["en"],
    )
    output_box = gr.Textbox(
        label="Recognized Text",
        lines=30,
    )

    return gr.Interface(
        fn=run_ocr_on_files,
        inputs=[file_input, language_select],
        outputs=output_box,
        title="OCR Text Extractor",
        description=(
            "Upload PDF documents or images to extract text using EasyOCR. "
            "Models are downloaded on first use and cached locally."
        ),
        allow_flagging="never",
    )


def launch_app() -> None:
    demo = build_interface()
    demo.launch()


if __name__ == "__main__":
    launch_app()
