from __future__ import annotations

from assistant.agent.state import AgentPlan, PlanStep


class AgentPlanner:
    def create_plan(self, user_request: str, file_path: str | None = None, audio_file_path: str | None = None) -> AgentPlan:
        text = user_request.lower()
        steps: list[PlanStep] = []
        goal = "Complete a local document, speech, retrieval, and reporting workflow"
        suffix = (file_path or "").lower()
        audio_suffix = (audio_file_path or "").lower()
        has_audio = bool(audio_file_path) or "audio" in text or "recording" in text or audio_suffix.endswith((".wav", ".mp3", ".m4a", ".flac"))
        is_document = bool(file_path or any(term in text for term in ["document", "pdf", "resume", "invoice", "receipt"]))
        if has_audio and not is_document and suffix.endswith((".wav", ".mp3", ".m4a", ".flac")):
            steps.append(PlanStep(tool="tool_transcribe_audio", reason="The request or input appears to include audio."))
        else:
            steps.append(PlanStep(tool="tool_ocr_document", reason="The input may contain document text or image content."))
            if has_audio:
                steps.append(PlanStep(tool="tool_transcribe_audio", reason="The recording may contain instructions for how to change the document."))
        if "translate" in text:
            steps.append(PlanStep(tool="tool_translate_text", reason="The user asked for English translation."))
        steps.append(PlanStep(tool="tool_chunk_document", reason="The content should be split into searchable sections."))
        if any(term in text for term in ["search", "find", "field", "extract", "vendor", "date", "total", "question", "summarize", "summary", "report"]):
            steps.append(PlanStep(tool="tool_search_document_chunks", reason="Relevant evidence should be retrieved from chunks."))
        if any(term in text for term in ["summarize", "summary", "extract", "field", "answer", "read"]):
            steps.append(PlanStep(tool="tool_summarize_document", reason="The user asked for a summary, answer, or extracted fields."))
        if "resume" in text and any(term in text for term in ["change", "update", "revise", "recording", "audio"]):
            steps.append(PlanStep(tool="tool_update_resume_from_instruction", reason="The user wants the resume changed using the recording or extracted instruction."))
        if "evaluate" in text or "quality" in text:
            steps.append(PlanStep(tool="tool_evaluate_output", reason="The user asked to evaluate output quality."))
        if "report" in text or True:
            steps.append(PlanStep(tool="tool_generate_report", reason="A persistent structured report is useful for this workflow."))
        return AgentPlan(goal=goal, steps=steps)
