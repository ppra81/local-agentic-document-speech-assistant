from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    source_file: str
    text: str
    start_char: int = 0
    end_char: int = 0
    metadata: dict = Field(default_factory=dict)


class SearchResult(DocumentChunk):
    score: float
    snippet: str

