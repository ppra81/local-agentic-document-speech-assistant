from __future__ import annotations

from assistant.adapters.mock_asr_adapter import MockASRAdapter
from assistant.tools.base import AssistantTool


class TranscribeAudioTool(AssistantTool):
    name = "tool_transcribe_audio"
    description = "Transcribe a local audio file using a mock ASR adapter."
    input_schema = {"file_path": "str"}
    output_schema = {"transcript": "str", "language": "str", "confidence": "float"}

    def __init__(self) -> None:
        self.adapter = MockASRAdapter()

    def run(self, input_data: dict) -> dict:
        return self.adapter.predict(input_data)

