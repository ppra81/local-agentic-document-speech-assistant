from __future__ import annotations

from typing import Any

from assistant.adapters.base import OptionalDependencyAdapter
from assistant.adapters.mock_asr_adapter import MockASRAdapter


class WhisperASRAdapter(OptionalDependencyAdapter):
    name = "whisper_asr_optional"
    task = "asr"
    dependency_name = "whisper"

    def predict(self, input_data: dict[str, Any]) -> dict[str, Any]:
        if not self.dependency_available():
            output = MockASRAdapter().predict(input_data)
            output["warning"] = self.fallback_message()
            return output
        import whisper  # type: ignore

        model_name = input_data.get("model_name", "base")
        model = whisper.load_model(model_name)
        result = model.transcribe(input_data["file_path"])
        return {"transcript": result.get("text", ""), "language": result.get("language", "unknown"), "confidence": 0.0, "adapter": self.name}

