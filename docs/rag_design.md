# RAG Design

RAG is intentionally local and lightweight:

- Documents are chunked with configurable size and overlap.
- Chunks are persisted in JSON.
- Search uses keyword overlap scoring.
- Results include source file, chunk id, snippet, and score.

The `Retriever` interface can later be backed by FAISS, ChromaDB, LanceDB, or another vector database.

