from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from assistant.adapters.local_rule_based_adapter import LocalRuleBasedAdapter
from assistant.config import settings
from assistant.tools.base import AssistantTool
from assistant.utils.ids import new_id


class UpdateResumeFromInstructionTool(AssistantTool):
    name = "tool_update_resume_from_instruction"
    description = "Update a resume/profile document using transcribed audio or text instructions."
    input_schema = {"resume_text": "str", "instruction": "str", "source_file": "str optional"}
    output_schema = {"updated_resume_markdown": "str", "updated_resume_path": "str", "updated_resume_pdf_path": "str", "changes": "list"}

    def __init__(self) -> None:
        self.adapter = LocalRuleBasedAdapter()

    def run(self, input_data: dict) -> dict:
        resume_text = input_data.get("resume_text") or input_data.get("text", "")
        instruction = input_data.get("instruction") or input_data.get("transcript") or input_data.get("request", "")
        source_file = input_data.get("source_file") or input_data.get("file_path") or "uploaded_resume"
        fields = self.adapter.extract_resume_fields(resume_text)
        changes = self._infer_changes(instruction)
        updated = self._build_updated_resume(resume_text, fields, instruction, changes, source_file)
        artifact_id = new_id("updated_resume")
        path = settings.reports_dir / f"{artifact_id}.md"
        pdf_path = settings.reports_dir / f"{artifact_id}.pdf"
        path.write_text(updated, encoding="utf-8")
        self._write_simple_pdf(pdf_path, updated)
        return {
            "updated_resume_markdown": updated,
            "updated_resume_path": str(path),
            "updated_resume_pdf_path": str(pdf_path),
            "changes": changes,
            "instruction_used": instruction,
            "fields": fields,
        }

    def _infer_changes(self, instruction: str) -> list[str]:
        lowered = instruction.lower()
        changes: list[str] = []
        if any(term in lowered for term in ["agentic", "agent", "tool calling", "workflow"]):
            changes.append("Add agentic AI and tool-calling experience.")
        if "rag" in lowered or "retrieval" in lowered:
            changes.append("Emphasize RAG and source-grounded retrieval.")
        if any(term in lowered for term in ["speech", "audio", "asr", "recording"]):
            changes.append("Emphasize speech-to-text and ASR evaluation experience.")
        if any(term in lowered for term in ["fastapi", "backend", "api"]):
            changes.append("Emphasize FastAPI/backend production engineering.")
        if any(term in lowered for term in ["evaluation", "eval", "quality", "metrics"]):
            changes.append("Strengthen evaluation framework and quality metrics positioning.")
        if any(term in lowered for term in ["recruiter", "portfolio", "project"]):
            changes.append("Make the resume more recruiter-facing and project-oriented.")
        return changes or ["Apply the supplied instruction while preserving the original resume facts."]

    def _build_updated_resume(self, resume_text: str, fields: dict[str, str], instruction: str, changes: list[str], source_file: str) -> str:
        name = fields.get("candidate_name", "Candidate")
        role = fields.get("target_role", "AI/ML Professional")
        skills = fields.get("skills", "Python, ML systems, evaluation, document AI, speech workflows")
        timestamp = datetime.now(timezone.utc).isoformat()
        agentic_section = "\n".join(
            [
                "## Agentic AI Resume Update",
                "",
                f"Target positioning: {role}",
                "",
                "### Updated Profile",
                (
                    f"{name} is positioned as an AI systems engineer who can connect document intelligence, speech processing, "
                    "RAG, tool calling, evaluation, and backend APIs into practical local-first workflows. The profile highlights "
                    "workflow intelligence: planning tool calls, extracting document evidence, transcribing user instructions, "
                    "updating structured outputs, evaluating quality, and generating auditable reports."
                ),
                "",
                "### Added / Strengthened Experience Bullets",
                "- Built local-first agentic AI workflows that connect OCR, ASR, translation, retrieval, summarization, evaluation, and report generation.",
                "- Designed tool-calling pipelines where an agent plans document extraction, audio transcription, resume revision, source-grounded retrieval, and quality checks.",
                "- Implemented RAG-style evidence retrieval with citations, chunk scores, source files, and unsupported-claim handling.",
                "- Developed evaluation-integrated AI systems with field accuracy, OCR CER, ASR WER/CER, retrieval hit rate, and summary coverage scoring.",
                "- Built production-style FastAPI and CLI interfaces for modular AI tools, local persistence, and downloadable Markdown/JSON reports.",
                "",
                "### Instruction Extracted From Recording",
                instruction.strip() or "No transcript was available from the recording. Mock/local ASR fallback was used.",
                "",
                "### Changes Applied",
                *[f"- {change}" for change in changes],
                "",
                "### Skills To Surface",
                skills,
                "",
                "---",
                "",
                "## Original Resume Text",
                "",
                resume_text.strip(),
                "",
                f"_Generated locally from {Path(source_file).name} at {timestamp}._",
            ]
        )
        return agentic_section

    def _write_simple_pdf(self, path: Path, text: str) -> None:
        lines = self._wrap_lines(text)
        objects: list[str] = [
            "<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        content_lines = ["BT", "/F1 10 Tf", "50 750 Td", "12 TL"]
        for line in lines[:56]:
            content_lines.append(f"({self._pdf_escape(line)}) Tj")
            content_lines.append("T*")
        content_lines.append("ET")
        stream = "\n".join(content_lines)
        objects.append(f"<< /Length {len(stream.encode('latin-1', errors='replace'))} >>\nstream\n{stream}\nendstream")
        pdf = "%PDF-1.4\n"
        offsets = [0]
        for idx, obj in enumerate(objects, 1):
            offsets.append(len(pdf.encode("latin-1")))
            pdf += f"{idx} 0 obj\n{obj}\nendobj\n"
        xref_start = len(pdf.encode("latin-1"))
        pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
        for offset in offsets[1:]:
            pdf += f"{offset:010d} 00000 n \n"
        pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n"
        path.write_bytes(pdf.encode("latin-1", errors="replace"))

    def _wrap_lines(self, text: str, width: int = 92) -> list[str]:
        output: list[str] = []
        for raw in text.replace("\r\n", "\n").splitlines():
            line = raw.strip()
            if not line:
                output.append("")
                continue
            while len(line) > width:
                split_at = line.rfind(" ", 0, width)
                if split_at <= 0:
                    split_at = width
                output.append(line[:split_at])
                line = line[split_at:].strip()
            output.append(line)
        return output

    def _pdf_escape(self, text: str) -> str:
        safe = text.encode("latin-1", errors="replace").decode("latin-1")
        return safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
