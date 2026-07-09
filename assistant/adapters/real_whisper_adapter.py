from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from assistant.adapters.base import ModelAdapter


class RealWhisperASRAdapter(ModelAdapter):
    name = "real_whisper_asr"
    task = "asr"

    def predict(self, input_data: dict[str, Any]) -> dict[str, Any]:
        file_path = input_data.get("file_path")
        if not file_path or not Path(file_path).exists():
            return {"transcript": "", "language": "unknown", "confidence": 0.0, "adapter": self.name, "warning": "Audio file was not found on the server."}

        python_executable = self._find_python()
        if not python_executable:
            return {
                "transcript": "",
                "language": "unknown",
                "confidence": 0.0,
                "adapter": self.name,
                "warning": "Real ASR is unavailable. Install openai-whisper/faster-whisper or set ASSISTANT_WHISPER_PYTHON.",
            }

        model_name = input_data.get("model_name") or os.getenv("ASSISTANT_WHISPER_MODEL", "base")
        code = """
import json, sys
audio_path = sys.argv[1]
model_name = sys.argv[2]
try:
    import whisper
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)
    print(json.dumps({"transcript": result.get("text", "").strip(), "language": result.get("language", "unknown"), "backend": "openai-whisper"}))
except Exception as first_error:
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        print(json.dumps({"transcript": text, "language": getattr(info, "language", "unknown"), "backend": "faster-whisper"}))
    except Exception as second_error:
        print(json.dumps({"error": f"{first_error} | {second_error}"}))
        sys.exit(2)
"""
        try:
            completed = subprocess.run(
                [str(python_executable), "-c", code, str(Path(file_path).resolve()), model_name],
                check=False,
                capture_output=True,
                text=True,
                timeout=int(os.getenv("ASSISTANT_WHISPER_TIMEOUT_SECONDS", "600")),
            )
        except subprocess.TimeoutExpired:
            return {"transcript": "", "language": "unknown", "confidence": 0.0, "adapter": self.name, "warning": "Real ASR timed out while transcribing audio."}

        if completed.returncode != 0:
            detail = completed.stdout.strip() or completed.stderr.strip()
            return {"transcript": "", "language": "unknown", "confidence": 0.0, "adapter": self.name, "warning": f"Real ASR failed: {detail}"}

        try:
            payload = json.loads(completed.stdout.strip().splitlines()[-1])
        except Exception:
            return {"transcript": "", "language": "unknown", "confidence": 0.0, "adapter": self.name, "warning": f"Real ASR returned invalid output: {completed.stdout[-500:]}"}

        if payload.get("error"):
            return {"transcript": "", "language": "unknown", "confidence": 0.0, "adapter": self.name, "warning": f"Real ASR failed: {payload['error']}"}
        return {
            "transcript": payload.get("transcript", ""),
            "language": payload.get("language", "unknown"),
            "confidence": 0.0,
            "adapter": payload.get("backend", self.name),
            "real_asr": True,
        }

    def _find_python(self) -> Path | None:
        candidates = []
        env_python = os.getenv("ASSISTANT_WHISPER_PYTHON")
        if env_python:
            candidates.append(Path(env_python))
        candidates.append(Path(sys.executable))
        project1_python = Path(__file__).resolve().parents[3] / "01_indic_dubbing_pipeline" / ".venv" / "Scripts" / "python.exe"
        candidates.append(project1_python)
        for candidate in candidates:
            if not candidate.exists():
                continue
            check = subprocess.run(
                [str(candidate), "-c", "import importlib.util; raise SystemExit(0 if (importlib.util.find_spec('whisper') or importlib.util.find_spec('faster_whisper')) else 1)"],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
            if check.returncode == 0:
                return candidate
        return None
