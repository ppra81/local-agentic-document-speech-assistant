from __future__ import annotations

from pathlib import Path
from typing import Any

from assistant.adapters.base import ModelAdapter


class MockOCRAdapter(ModelAdapter):
    name = "mock_ocr"
    task = "ocr"

    def predict(self, input_data: dict[str, Any]) -> dict[str, Any]:
        file_path = input_data.get("file_path")
        text = input_data.get("text", "")
        if file_path and Path(file_path).exists():
            try:
                text = Path(file_path).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = f"[mock OCR text extracted from binary file: {Path(file_path).name}]"
        return {"text": text, "confidence": 0.98, "adapter": self.name}

