from assistant.tools.ocr_tool import OCRDocumentTool


def test_ocr_tool_reads_text_file(tmp_path):
    file_path = tmp_path / "doc.txt"
    file_path.write_text("Vendor: Test Store", encoding="utf-8")
    output = OCRDocumentTool().run({"file_path": str(file_path)})
    assert "Test Store" in output["text"]

