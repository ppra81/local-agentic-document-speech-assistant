from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from assistant.api.schemas import AudioTranscribeRequest
from assistant.config import settings
from assistant.tools.asr_tool import TranscribeAudioTool

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/transcribe")
def transcribe_audio(payload: AudioTranscribeRequest) -> dict:
    return TranscribeAudioTool().run({"file_path": payload.file_path, "text": payload.text})


@router.post("/transcribe-upload")
async def transcribe_audio_upload(file: UploadFile = File(...)) -> dict:
    content = await file.read()
    text = ""
    if (file.content_type or "").startswith("text") or (file.filename or "").lower().endswith((".txt", ".md")):
        text = content.decode("utf-8", errors="replace")
        return TranscribeAudioTool().run({"file_path": file.filename, "text": text})
    upload_dir = settings.data_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "uploaded_audio.m4a").name
    path = upload_dir / safe_name
    path.write_bytes(content)
    return TranscribeAudioTool().run({"file_path": str(path), "text": ""})
