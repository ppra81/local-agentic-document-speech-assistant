from assistant.agent.executor import AgentExecutor


def test_agent_updates_resume_from_recording_instruction():
    resume_text = """Praneeth Reddy
Data Scientist
praneeth@example.com
SUMMARY
Data Scientist with 3+ years at IIT Madras.
TECHNICAL SKILLS
Python, PyTorch, Hugging Face
PROFESSIONAL EXPERIENCE
Project Associate — AI4Bharat
EDUCATION
B.E., ECE | CGPA: 7.5
"""
    result = AgentExecutor().run(
        "Read this resume, transcribe the recording, update the resume as per the recording, evaluate quality, and generate a report.",
        file_path="resume.pdf",
        input_text=resume_text,
        audio_file_path="recording.m4a",
        audio_text="Update the resume to emphasize agentic AI, RAG, tool calling, FastAPI backend engineering, and evaluation metrics.",
    )

    tools = [step["tool"] for step in result.plan["steps"]]
    assert "tool_transcribe_audio" in tools
    assert "tool_update_resume_from_instruction" in tools
    assert result.answer == "Updated resume generated from the document and recording instruction."
    assert "updated_resume_path" in result.report["report"]["final_answer"]
    assert "updated_resume_pdf_path" in result.report["report"]["final_answer"]


def test_agent_applies_experience_change_to_resume_summary():
    resume_text = """Praneeth Reddy
Data Scientist
SUMMARY
Data Scientist with 3+ years at IIT Madras.
TECHNICAL SKILLS
Python
PROFESSIONAL EXPERIENCE
Project Associate
"""
    result = AgentExecutor().run(
        "Read this resume, update the resume as per the recording.",
        file_path="resume.pdf",
        input_text=resume_text,
        audio_file_path="recording.m4a",
        audio_text="change the experience to 4 years in the summary of the resume PDF.",
    )

    output = result.report["report"]["intermediate_outputs"]["tool_update_resume_from_instruction"]
    assert "Data Scientist with 4 years at IIT Madras." in output["updated_resume_markdown"]
    assert result.summary == "Data Scientist with 4 years at IIT Madras."
    assert output["fields"]["experience"] == "4 years"
    assert any("3+ years to 4 years" in change for change in output["changes"])
