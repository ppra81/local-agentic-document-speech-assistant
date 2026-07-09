from assistant.rag.chunker import chunk_text
from assistant.rag.index import LocalKeywordIndex
from assistant.rag.retriever import Retriever


def test_retrieval_can_scope_to_current_document(tmp_path):
    retriever = Retriever(LocalKeywordIndex(tmp_path / "index.json"))
    retriever.index("doc_invoice", chunk_text("Vendor: Example Medical Store Total Amount 1250", "doc_invoice", "invoice.txt"))
    retriever.index("doc_resume", chunk_text("Machine learning computer vision resume", "doc_resume", "resume.pdf"))

    results = retriever.search("vendor total resume", document_id="doc_resume")

    assert results
    assert all(item["document_id"] == "doc_resume" for item in results)
    assert "Medical Store" not in results[0]["text"]
