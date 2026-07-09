from __future__ import annotations

import json
from pathlib import Path

from assistant.config import settings
from assistant.rag.schemas import DocumentChunk


class LocalKeywordIndex:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.data_dir / "rag_index.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._chunks: list[DocumentChunk] = []
        self.load()

    def load(self) -> None:
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self._chunks = [DocumentChunk(**item) for item in data]

    def save(self) -> None:
        self.path.write_text(json.dumps([c.model_dump() for c in self._chunks], indent=2), encoding="utf-8")

    def upsert(self, chunks: list[DocumentChunk]) -> None:
        ids = {c.chunk_id for c in chunks}
        self._chunks = [c for c in self._chunks if c.chunk_id not in ids] + chunks
        self.save()

    def all_chunks(self) -> list[DocumentChunk]:
        return list(self._chunks)

