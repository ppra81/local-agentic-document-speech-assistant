from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

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
        updated_resume_text, edit = self._apply_instruction_edits(resume_text, instruction)
        fields = self.adapter.extract_resume_fields(updated_resume_text)
        changes = self._infer_changes(instruction, edit)
        updated = self._build_updated_resume(updated_resume_text, fields, instruction, changes, source_file)
        artifact_id = new_id("updated_resume")
        path = settings.reports_dir / f"{artifact_id}.md"
        pdf_path = settings.reports_dir / f"{artifact_id}.pdf"
        path.write_text(updated, encoding="utf-8")
        self._write_updated_pdf(pdf_path, updated, updated_resume_text, source_file, edit)
        return {
            "updated_resume_markdown": updated,
            "updated_resume_path": str(path),
            "updated_resume_pdf_path": str(pdf_path),
            "updated_summary": self._extract_summary(updated_resume_text),
            "changes": changes,
            "instruction_used": instruction,
            "fields": fields,
        }

    def _infer_changes(self, instruction: str, edit: dict[str, str] | None = None) -> list[str]:
        lowered = instruction.lower()
        changes: list[str] = []
        if edit:
            changes.append(f"Update experience from {edit['old']} to {edit['new']} in the resume summary.")
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
                "## Updated Resume Text",
                "",
                resume_text.strip(),
                "",
                f"_Generated locally from {Path(source_file).name} at {timestamp}._",
            ]
        )
        return agentic_section

    def _apply_instruction_edits(self, resume_text: str, instruction: str) -> tuple[str, dict[str, str] | None]:
        target = self._target_experience(instruction)
        if not target:
            return resume_text, None
        updated, old = self._replace_summary_experience(resume_text, target)
        if not old:
            return resume_text, None
        return updated, {"old": old, "new": target}

    def _target_experience(self, instruction: str) -> str | None:
        patterns = [
            r"\bexperience\b[^.\n]*?\b(?:to|as)\s+(\d+\+?\s*(?:years?|yrs?))\b",
            r"\b(?:to|as)\s+(\d+\+?\s*(?:years?|yrs?))\b[^.\n]*?\bexperience\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, instruction, flags=re.IGNORECASE)
            if match:
                value = re.sub(r"\s+", " ", match.group(1)).strip()
                return re.sub(r"\byrs?\b", "years", value, flags=re.IGNORECASE)
        return None

    def _replace_summary_experience(self, resume_text: str, target: str) -> tuple[str, str | None]:
        summary = re.search(
            r"(?P<prefix>^SUMMARY\s*\n)(?P<body>.*?)(?=\n[A-Z][A-Z &/+-]{3,}\s*\n|\Z)",
            resume_text,
            flags=re.DOTALL | re.MULTILINE,
        )
        experience_pattern = re.compile(r"\b\d+\+?\s*(?:years?|yrs?)\b", flags=re.IGNORECASE)
        if summary:
            body = summary.group("body")
            match = experience_pattern.search(body)
            if match:
                new_body = body[: match.start()] + target + body[match.end() :]
                return resume_text[: summary.start("body")] + new_body + resume_text[summary.end("body") :], match.group(0)
        match = experience_pattern.search(resume_text)
        if not match:
            return resume_text, None
        return resume_text[: match.start()] + target + resume_text[match.end() :], match.group(0)

    def _extract_summary(self, resume_text: str) -> str:
        summary = re.search(
            r"^SUMMARY\s*\n(?P<body>.*?)(?=\n[A-Z][A-Z &/+-]{3,}\s*\n|\Z)",
            resume_text,
            flags=re.DOTALL | re.MULTILINE,
        )
        if summary:
            return re.sub(r"\s+", " ", summary.group("body")).strip()
        return ""

    def _write_updated_pdf(
        self,
        path: Path,
        markdown_text: str,
        updated_resume_text: str,
        source_file: str,
        edit: dict[str, str] | None,
    ) -> None:
        source_path = Path(source_file)
        if edit and source_path.exists() and source_path.suffix.lower() == ".pdf":
            if self._write_preserving_pdf(path, source_path, edit["old"], edit["new"]):
                return
        self._write_simple_pdf(path, updated_resume_text if updated_resume_text.strip() else markdown_text)

    def _write_preserving_pdf(self, output_path: Path, source_path: Path, old_text: str, new_text: str) -> bool:
        try:
            import fitz  # type: ignore
        except Exception:
            return False
        try:
            with fitz.open(source_path) as document:
                changed = False
                for page in document:
                    rects = page.search_for(old_text)
                    for rect in rects:
                        page.add_redact_annot(rect, fill=(1, 1, 1))
                        changed = True
                    if rects:
                        page.apply_redactions()
                        for rect in rects:
                            page.insert_textbox(
                                rect,
                                new_text,
                                fontsize=max(8, min(11, rect.height * 0.72)),
                                fontname="helv",
                                color=(0, 0, 0),
                                align=0,
                            )
                if not changed:
                    return False
                document.save(output_path, garbage=4, deflate=True)
            return True
        except Exception:
            return False

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
