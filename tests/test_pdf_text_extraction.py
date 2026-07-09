from pathlib import Path

from assistant.api.routes_documents import extract_text_from_upload_bytes


def test_simple_pdf_upload_sample_extracts_text():
    content = Path("examples/upload_sample_invoice.pdf").read_bytes()
    text = extract_text_from_upload_bytes(content, "upload_sample_invoice.pdf")
    assert "Vendor: Example Medical Store" in text
    assert "Total Amount: INR 1,250" in text
