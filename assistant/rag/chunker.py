from __future__ import annotations

from pathlib import Path

from assistant.rag.schemas import DocumentChunk
from assistant.utils.text import normalize_text


def chunk_text(text: str, document_id: str, source_file: str, chunk_size: int = 550, overlap: int = 80) -> list[DocumentChunk]:
    clean = normalize_text(text)
    if not clean:
        return []
    chunks: list[DocumentChunk] = []
    start = 0
    idx = 1
    step = max(chunk_size - overlap, 1)
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunk = clean[start:end]
        chunks.append(
            DocumentChunk(
                chunk_id=f"{document_id}_chunk_{idx:03d}",
                document_id=document_id,
                source_file=Path(source_file).name,
                text=chunk,
                start_char=start,
                end_char=end,
            )
        )
        if end == len(clean):
            break
        start += step
        idx += 1
    return chunks

