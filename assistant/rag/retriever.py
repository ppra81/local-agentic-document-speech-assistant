from __future__ import annotations

from assistant.rag.index import LocalKeywordIndex
from assistant.rag.schemas import DocumentChunk, SearchResult
from assistant.utils.text import keyword_score


class Retriever:
    def __init__(self, index_store: LocalKeywordIndex | None = None) -> None:
        self.index_store = index_store or LocalKeywordIndex()

    def index(self, document_id: str, chunks: list[dict] | list[DocumentChunk]) -> None:
        parsed = [c if isinstance(c, DocumentChunk) else DocumentChunk(**c) for c in chunks]
        self.index_store.upsert(parsed)

    def search(self, query: str, top_k: int = 5, document_id: str | None = None) -> list[dict]:
        results: list[SearchResult] = []
        for chunk in self.index_store.all_chunks():
            if document_id and chunk.document_id != document_id:
                continue
            score = keyword_score(query, chunk.text)
            if score > 0:
                results.append(SearchResult(**chunk.model_dump(), score=score, snippet=chunk.text[:220]))
        results.sort(key=lambda item: item.score, reverse=True)
        return [r.model_dump() for r in results[:top_k]]
