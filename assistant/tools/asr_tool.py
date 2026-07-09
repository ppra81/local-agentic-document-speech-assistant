from __future__ import annotations

from pathlib import Path

from assistant.adapters.mock_asr_adapter import MockASRAdapter
from assistant.adapters.real_whisper_adapter import RealWhisperASRAdapter
from assistant.tools.base import AssistantTool


class TranscribeAudioTool(AssistantTool):
    name = "tool_transcribe_audio"
    description = "Transcribe a local audio file using a mock ASR adapter."
    input_schema = {"file_path": "str"}
    output_schema = {"transcript": "str", "language": "str", "confidence": "float"}

    def __init__(self) -> None:
        self.mock_adapter = MockASRAdapter()
        self.real_adapter = RealWhisperASRAdapter()

    def run(self, input_data: dict) -> dict:
        if input_data.get("text"):
            return self.mock_adapter.predict(input_data)
        file_path = input_data.get("file_path")
        if file_path and Path(file_path).exists() and Path(file_path).suffix.lower() in {".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg"}:
            output = self.real_adapter.predict(input_data)
            if output.get("transcript"):
                return output
            output["fallback_available"] = "Paste a transcript manually, upload a .txt transcript, or install/download a Whisper model."
            return output
        return self.mock_adapter.predict(input_data)
