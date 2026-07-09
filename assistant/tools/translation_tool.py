from __future__ import annotations

from assistant.adapters.mock_translation_adapter import MockTranslationAdapter
from assistant.tools.base import AssistantTool


class TranslateTextTool(AssistantTool):
    name = "tool_translate_text"
    description = "Translate free text to English using a mock translation adapter."
    input_schema = {"text": "str", "target_language": "str"}
    output_schema = {"text": "str", "target_language": "str"}

    def __init__(self) -> None:
        self.adapter = MockTranslationAdapter()

    def run(self, input_data: dict) -> dict:
        return self.adapter.predict(input_data)


class TranslateFieldsTool(AssistantTool):
    name = "tool_translate_fields"
    description = "Translate structured fields to English using a mock translation adapter."
    input_schema = {"fields": "dict", "target_language": "str"}
    output_schema = {"fields": "dict", "target_language": "str"}

    def __init__(self) -> None:
        self.adapter = MockTranslationAdapter()

    def run(self, input_data: dict) -> dict:
        return self.adapter.predict(input_data)

