from assistant.agent.planner import AgentPlanner


def test_planner_creates_valid_steps():
    plan = AgentPlanner().create_plan("Read this invoice, extract vendor, total, summarize, and generate report.", "invoice.txt")
    tools = [step.tool for step in plan.steps]
    assert tools[0] == "tool_ocr_document"
    assert "tool_chunk_document" in tools
    assert "tool_search_document_chunks" in tools
    assert "tool_generate_report" in tools


def test_planner_schedules_generic_pdf_edit_workflow():
    plan = AgentPlanner().create_plan("Read this PDF, transcribe the recording, update the PDF as instructed.", "resume.pdf", "voice.m4a")
    tools = [step.tool for step in plan.steps]
    assert "tool_transcribe_audio" in tools
    assert "tool_update_resume_from_instruction" in tools
