from __future__ import annotations

from typing import Any

from assistant.adapters.base import ModelAdapter


class MockTranslationAdapter(ModelAdapter):
    name = "mock_translation"
    task = "translation"

    def predict(self, input_data: dict[str, Any]) -> dict[str, Any]:
        text = input_data.get("text", "")
        fields = input_data.get("fields")
        if isinstance(fields, dict):
            return {"fields": fields, "target_language": "en", "adapter": self.name}
        return {"text": text, "target_language": "en", "adapter": self.name}

