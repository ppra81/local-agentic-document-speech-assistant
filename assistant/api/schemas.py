from __future__ import annotations

from pydantic import BaseModel


class AgentAskRequest(BaseModel):
    request: str
    file_path: str | None = None
    text: str | None = None
    audio_file_path: str | None = None
    audio_text: str | None = None
    reference: dict | None = None


class IngestRequest(BaseModel):
    file_path: str | None = None
    text: str | None = None
    source_file: str = "uploaded_text.txt"


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class AudioTranscribeRequest(BaseModel):
    file_path: str | None = None
    text: str | None = None


class ReportRequest(BaseModel):
    file_path: str | None = None
    text: str | None = None
    audio_file_path: str | None = None
    audio_text: str | None = None
    request: str = "Extract the important fields and summarize the document."


class EvaluateRequest(BaseModel):
    prediction: dict
    reference: dict = {}
