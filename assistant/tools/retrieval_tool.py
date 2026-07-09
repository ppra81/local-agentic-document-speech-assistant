from __future__ import annotations

from assistant.rag.retriever import Retriever
from assistant.tools.base import AssistantTool


class SearchDocumentChunksTool(AssistantTool):
    name = "tool_search_document_chunks"
    description = "Index chunks if supplied and run keyword search with citations."
    input_schema = {"query": "str", "chunks": "list optional", "top_k": "int"}
    output_schema = {"results": "list"}

    def __init__(self) -> None:
        self.retriever = Retriever()

    def run(self, input_data: dict) -> dict:
        chunks = input_data.get("chunks") or []
        document_id = input_data.get("document_id", "doc_inline")
        if chunks:
            self.retriever.index(document_id, chunks)
        return {"results": self.retriever.search(input_data.get("query", ""), int(input_data.get("top_k", 5)), document_id if chunks else None)}
