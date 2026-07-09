from __future__ import annotations

from pathlib import Path
from typing import Any

from assistant.adapters.base import ModelAdapter


class MockASRAdapter(ModelAdapter):
    name = "mock_asr"
    task = "asr"

    def predict(self, input_data: dict[str, Any]) -> dict[str, Any]:
        file_path = input_data.get("file_path")
        if input_data.get("text"):
            transcript = input_data["text"]
        elif file_path and Path(file_path).suffix.lower() in {".txt", ".md"} and Path(file_path).exists():
            transcript = Path(file_path).read_text(encoding="utf-8")
        else:
            transcript = (
                "Mock transcript generated locally for the supplied audio file. "
                "Instruction: update the resume to emphasize agentic AI, RAG, tool calling, speech-to-text workflows, "
                "evaluation metrics, FastAPI backend engineering, and recruiter-ready project impact."
            )
        return {"transcript": transcript, "language": "en", "confidence": 0.9, "adapter": self.name}
