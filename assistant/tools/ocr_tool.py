from __future__ import annotations

from pathlib import Path

from assistant.tools.base import AssistantTool


class OCRDocumentTool(AssistantTool):
    name = "tool_ocr_document"
    description = "Read extracted upload text or a local text document."
    input_schema = {"file_path": "str optional", "text": "str optional"}
    output_schema = {"text": "str", "confidence": "float"}

    def run(self, input_data: dict) -> dict:
        text = input_data.get("text") or ""
        if text:
            return {"text": text, "confidence": 1.0, "adapter": "uploaded_text"}
        file_path = input_data.get("file_path")
        if file_path and Path(file_path).exists():
            try:
                return {"text": Path(file_path).read_text(encoding="utf-8"), "confidence": 1.0, "adapter": "text_file"}
            except UnicodeDecodeError:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "adapter": "text_file",
                    "warning": "Binary document path requires upload extraction or an OCR/PDF parser.",
                }
        return {"text": "", "confidence": 0.0, "adapter": "uploaded_text", "warning": "No document text was provided."}
