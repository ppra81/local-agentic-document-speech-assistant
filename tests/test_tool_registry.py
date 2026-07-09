from assistant.tools import build_tool_registry


def test_tool_registry_loads_tools():
    names = build_tool_registry().names()
    assert "tool_ocr_document" in names
    assert "tool_generate_report" in names
    assert "tool_update_resume_from_instruction" in names
    assert len(names) == 10
