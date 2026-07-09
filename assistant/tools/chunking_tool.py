from __future__ import annotations

from assistant.config import settings
from assistant.rag.chunker import chunk_text
from assistant.tools.base import AssistantTool
from assistant.utils.ids import stable_file_id


class ChunkDocumentTool(AssistantTool):
    name = "tool_chunk_document"
    description = "Split document text into retrievable chunks."
    input_schema = {"text": "str", "file_path": "str optional"}
    output_schema = {"document_id": "str", "chunks": "list"}

    def run(self, input_data: dict) -> dict:
        file_path = input_data.get("file_path", "inline_document.txt")
        document_id = input_data.get("document_id") or stable_file_id(file_path)
        chunks = chunk_text(input_data.get("text", ""), document_id, file_path, settings.chunk_size, settings.chunk_overlap)
        return {"document_id": document_id, "chunks": [c.model_dump() for c in chunks]}

