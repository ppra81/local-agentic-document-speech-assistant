from __future__ import annotations

from assistant.adapters.mock_ocr_adapter import MockOCRAdapter
from assistant.tools.base import AssistantTool


class OCRDocumentTool(AssistantTool):
    name = "tool_ocr_document"
    description = "Extract text from a local document or image using a mock/local OCR adapter."
    input_schema = {"file_path": "str optional", "text": "str optional"}
    output_schema = {"text": "str", "confidence": "float"}

    def __init__(self) -> None:
        self.adapter = MockOCRAdapter()

    def run(self, input_data: dict) -> dict:
        return self.adapter.predict(input_data)

