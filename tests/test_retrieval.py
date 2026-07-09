from assistant.rag.index import LocalKeywordIndex
from assistant.rag.retriever import Retriever
from assistant.rag.chunker import chunk_text


def test_retrieval_returns_relevant_chunks(tmp_path):
    index = LocalKeywordIndex(tmp_path / "index.json")
    retriever = Retriever(index)
    chunks = chunk_text("Total Amount: 1250. Vendor: Example Store.", "doc1", "invoice.txt")
    retriever.index("doc1", chunks)
    results = retriever.search("total amount")
    assert results
    assert "Total Amount" in results[0]["text"]

