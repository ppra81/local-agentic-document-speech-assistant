from assistant.rag.chunker import chunk_text


def test_document_chunking_works():
    chunks = chunk_text("alpha beta gamma " * 80, "doc1", "source.txt", chunk_size=80, overlap=10)
    assert len(chunks) > 1
    assert chunks[0].chunk_id == "doc1_chunk_001"

