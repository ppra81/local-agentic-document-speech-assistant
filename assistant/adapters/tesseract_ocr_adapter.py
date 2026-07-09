from __future__ import annotations

from pathlib import Path
from typing import Any

from assistant.adapters.base import OptionalDependencyAdapter
from assistant.adapters.mock_ocr_adapter import MockOCRAdapter


class TesseractOCRAdapter(OptionalDependencyAdapter):
    name = "tesseract_ocr_optional"
    task = "ocr"
    dependency_name = "pytesseract"

    def predict(self, input_data: dict[str, Any]) -> dict[str, Any]:
        if not self.dependency_available():
            output = MockOCRAdapter().predict(input_data)
            output["warning"] = self.fallback_message()
            return output
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore

        file_path = Path(input_data["file_path"])
        text = pytesseract.image_to_string(Image.open(file_path))
        return {"text": text, "confidence": 0.0, "adapter": self.name}

