from __future__ import annotations

from pathlib import Path

from assistant.adapters.real_whisper_adapter import RealWhisperASRAdapter
from assistant.tools.base import AssistantTool


class TranscribeAudioTool(AssistantTool):
    name = "tool_transcribe_audio"
    description = "Transcribe a local audio file with Whisper/faster-whisper, or accept a user-provided transcript."
    input_schema = {"file_path": "str optional", "text": "str optional"}
    output_schema = {"transcript": "str", "language": "str", "confidence": "float"}

    def __init__(self) -> None:
        self.real_adapter = RealWhisperASRAdapter()

    def run(self, input_data: dict) -> dict:
        if input_data.get("text"):
            return {
                "transcript": input_data["text"],
                "language": "user_provided",
                "confidence": 1.0,
                "adapter": "provided_transcript",
            }
        file_path = input_data.get("file_path")
        if file_path and Path(file_path).exists() and Path(file_path).suffix.lower() in {".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg"}:
            output = self.real_adapter.predict(input_data)
            if output.get("transcript"):
                return output
            output["fallback_available"] = "Paste a transcript manually, upload a .txt transcript, or install/download a Whisper model."
            return output
        if file_path and Path(file_path).suffix.lower() in {".txt", ".md"} and Path(file_path).exists():
            return {
                "transcript": Path(file_path).read_text(encoding="utf-8"),
                "language": "user_provided",
                "confidence": 1.0,
                "adapter": "provided_transcript",
            }
        return {
            "transcript": "",
            "language": "unknown",
            "confidence": 0.0,
            "adapter": "real_asr",
            "warning": "No transcript was provided and no readable audio file was available.",
        }
