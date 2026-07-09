from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re

from assistant.adapters.local_rule_based_adapter import LocalRuleBasedAdapter
from assistant.config import settings
from assistant.tools.base import AssistantTool
from assistant.utils.ids import new_id


@dataclass(frozen=True)
class DocumentEdit:
    label: str
    old: str
    new: str
    scope: str = "document"
    replace_all: bool = False


class UpdateResumeFromInstructionTool(AssistantTool):
    name = "tool_update_resume_from_instruction"
    description = "Edit an uploaded document or resume PDF using transcribed audio or text instructions."
    input_schema = {"resume_text": "str", "instruction": "str", "source_file": "str optional"}
    output_schema = {"updated_resume_markdown": "str", "updated_resume_path": "str", "updated_resume_pdf_path": "str", "changes": "list"}

    def __init__(self) -> None:
        self.adapter = LocalRuleBasedAdapter()

    def run(self, input_data: dict) -> dict:
        document_text = input_data.get("resume_text") or input_data.get("text", "")
        instruction = input_data.get("instruction") or input_data.get("transcript") or input_data.get("request", "")
        source_file = input_data.get("source_file") or input_data.get("file_path") or "uploaded_document"
        edits = self._plan_edits(document_text, instruction)
        updated_text = self._apply_edits_to_text(document_text, edits)
        fields = self.adapter.extract_resume_fields(updated_text)
        changes = self._changes(edits)
        artifact_id = new_id("updated_resume")
        path = settings.reports_dir / f"{artifact_id}.md"
        pdf_path = settings.reports_dir / f"{artifact_id}.pdf"
        report = self._build_edit_report(updated_text, instruction, changes, source_file, edits)
        path.write_text(report, encoding="utf-8")
        pdf_result = self._write_updated_pdf(pdf_path, updated_text, source_file, edits)
        return {
            "updated_resume_markdown": report,
            "updated_resume_path": str(path),
            "updated_resume_pdf_path": str(pdf_path),
            "updated_summary": self._extract_summary(updated_text),
            "changes": changes,
            "instruction_used": instruction,
            "fields": fields,
            "edit_count": len(edits),
            "pdf_edit_status": pdf_result,
        }

    def _plan_edits(self, document_text: str, instruction: str) -> list[DocumentEdit]:
        edits: list[DocumentEdit] = []
        edits.extend(self._explicit_replacements(instruction))
        edits.extend(self._field_edits(document_text, instruction))
        return self._dedupe_edits(edits)

    def _explicit_replacements(self, instruction: str) -> list[DocumentEdit]:
        edits: list[DocumentEdit] = []
        quoted = re.finditer(
            r"(?:replace|change|update)\s+[\"'](?P<old>.+?)[\"']\s+(?:with|to)\s+[\"'](?P<new>.+?)[\"']",
            instruction,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for match in quoted:
            edits.append(DocumentEdit("explicit replacement", match.group("old").strip(), match.group("new").strip(), replace_all=True))

        plain = re.finditer(
            r"(?:replace|change|update)\s+(?P<old>[A-Za-z0-9][^.\n]{1,80}?)\s+(?:with|to)\s+(?P<new>[A-Za-z0-9][^.\n]{1,80})",
            instruction,
            flags=re.IGNORECASE,
        )
        for match in plain:
            old = self._clean_instruction_value(match.group("old"))
            new = self._clean_instruction_value(match.group("new"))
            if old and new and not self._looks_like_field_name(old):
                edits.append(DocumentEdit("explicit replacement", old, new, replace_all=True))
        return edits

    def _field_edits(self, document_text: str, instruction: str) -> list[DocumentEdit]:
        field_patterns = {
            "experience": r"\b\d+\+?\s*(?:years?|yrs?)\b",
            "email": r"[\w.\-+]+@[\w.\-]+\.\w+",
            "phone": r"(?:\+\d{1,3}\s*)?\d{10}",
        }
        edits: list[DocumentEdit] = []
        lowered = instruction.lower()
        for field, old_pattern in field_patterns.items():
            target = self._target_for_field(instruction, field)
            if not target:
                continue
            old = self._find_in_scope(document_text, old_pattern, self._scope_from_instruction(lowered))
            if old:
                edits.append(DocumentEdit(field, old, self._normalize_field_value(field, target), self._scope_from_instruction(lowered)))

        title_target = self._target_for_field(instruction, "title") or self._target_for_field(instruction, "role")
        if title_target:
            title_old = self._current_title(document_text)
            if title_old:
                edits.append(DocumentEdit("title", title_old, title_target, "header"))
        return edits

    def _target_for_field(self, instruction: str, field: str) -> str | None:
        aliases = {
            "experience": r"(?:experience|years?\s+of\s+experience)",
            "email": r"(?:email|mail)",
            "phone": r"(?:phone|mobile|contact\s+number)",
            "title": r"(?:title|headline|designation)",
            "role": r"(?:role)",
        }
        alias = aliases[field]
        patterns = [
            rf"\b{alias}\b[^.\n]*?\b(?:to|as)\s+(?P<value>[^.\n]+)",
            rf"\b(?:set|update|change)\s+(?:the\s+)?{alias}\s+(?:to|as)\s+(?P<value>[^.\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, instruction, flags=re.IGNORECASE)
            if match:
                return self._clean_instruction_value(match.group("value"))
        return None

    def _scope_from_instruction(self, lowered_instruction: str) -> str:
        if "summary" in lowered_instruction or "profile" in lowered_instruction:
            return "summary"
        if "header" in lowered_instruction:
            return "header"
        return "document"

    def _find_in_scope(self, document_text: str, pattern: str, scope: str) -> str | None:
        target_text = self._section_text(document_text, "SUMMARY") if scope == "summary" else document_text
        match = re.search(pattern, target_text, flags=re.IGNORECASE)
        return match.group(0) if match else None

    def _current_title(self, document_text: str) -> str | None:
        lines = [line.strip() for line in document_text.splitlines() if line.strip() and not set(line.strip()) <= {"_"}]
        if len(lines) > 1 and any(term in lines[1].lower() for term in ["scientist", "engineer", "research", "developer", "analyst", "manager"]):
            return lines[1]
        return None

    def _apply_edits_to_text(self, document_text: str, edits: list[DocumentEdit]) -> str:
        updated = document_text
        for edit in edits:
            if edit.scope == "summary":
                updated = self._replace_in_section(updated, "SUMMARY", edit.old, edit.new)
            elif edit.replace_all:
                updated = self._replace_all(updated, edit.old, edit.new)
            else:
                updated = self._replace_once(updated, edit.old, edit.new)
        return updated

    def _replace_in_section(self, text: str, section_name: str, old: str, new: str) -> str:
        section = re.search(
            rf"(?P<prefix>^{re.escape(section_name)}\s*\n)(?P<body>.*?)(?=\n[A-Z][A-Z &/+-]{{3,}}\s*\n|\Z)",
            text,
            flags=re.DOTALL | re.MULTILINE,
        )
        if not section:
            return self._replace_once(text, old, new)
        body = self._replace_once(section.group("body"), old, new)
        return text[: section.start("body")] + body + text[section.end("body") :]

    def _replace_once(self, text: str, old: str, new: str) -> str:
        pattern = re.compile(re.escape(old), flags=re.IGNORECASE)
        return pattern.sub(new, text, count=1)

    def _replace_all(self, text: str, old: str, new: str) -> str:
        pattern = re.compile(re.escape(old), flags=re.IGNORECASE)
        return pattern.sub(new, text)

    def _write_updated_pdf(self, path: Path, updated_text: str, source_file: str, edits: list[DocumentEdit]) -> dict:
        source_path = Path(source_file)
        if source_path.exists() and source_path.suffix.lower() == ".pdf" and edits:
            result = self._edit_existing_pdf(path, source_path, edits)
            if result["applied"]:
                return result
        self._write_simple_pdf(path, updated_text)
        return {
            "mode": "generated_text_pdf",
            "applied": 0,
            "requested": len(edits),
            "warning": "Could not edit the original PDF text layer. Generated a text PDF fallback.",
        }

    def _edit_existing_pdf(self, output_path: Path, source_path: Path, edits: list[DocumentEdit]) -> dict:
        try:
            import fitz  # type: ignore
        except Exception:
            return {"mode": "original_pdf", "applied": 0, "requested": len(edits), "warning": "PyMuPDF is not installed."}
        applied = 0
        try:
            with fitz.open(source_path) as document:
                for edit in edits:
                    applied += self._apply_pdf_edit(document, edit)
                if not applied:
                    return {"mode": "original_pdf", "applied": 0, "requested": len(edits), "warning": "No matching selectable PDF text found."}
                document.save(output_path, garbage=4, deflate=True)
            return {"mode": "original_pdf", "applied": applied, "requested": len(edits)}
        except Exception as exc:
            return {"mode": "original_pdf", "applied": applied, "requested": len(edits), "warning": str(exc)}

    def _apply_pdf_edit(self, document: object, edit: DocumentEdit) -> int:
        changed = 0
        for page in document:
            rects = page.search_for(edit.old)
            if not rects:
                continue
            targets = rects if edit.replace_all else rects[:1]
            styles = [(rect, self._style_for_match(page, rect, edit.old)) for rect in targets]
            for rect, _style in styles:
                page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()
            for _rect, style in styles:
                page.insert_text(
                    style["origin"],
                    edit.new,
                    fontsize=style["size"],
                    fontname="helv",
                    color=style["color"],
                )
                changed += 1
            if changed and not edit.replace_all:
                break
        return changed

    def _style_for_match(self, page: object, rect: object, old_text: str) -> dict:
        fallback = {
            "origin": (rect.x0, rect.y1 - max(1, rect.height * 0.2)),
            "size": max(6, rect.height * 0.72),
            "color": (0, 0, 0),
        }
        try:
            text = page.get_text("dict", clip=rect + (-2, -4, 2, 4))
        except Exception:
            return fallback
        normalized_old = self._normalize_match_text(old_text)
        best_span = None
        for block in text.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    if normalized_old in self._normalize_match_text(span_text):
                        best_span = span
                        break
                if best_span:
                    break
            if best_span:
                break
        if not best_span:
            return fallback
        origin = best_span.get("origin") or (rect.x0, rect.y1 - max(1, rect.height * 0.2))
        size = float(best_span.get("size") or fallback["size"])
        color = self._pdf_color(best_span.get("color", 0))
        return {"origin": (origin[0], origin[1]), "size": size, "color": color}

    def _normalize_match_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip().lower()

    def _pdf_color(self, color_value: int) -> tuple[float, float, float]:
        try:
            red = ((int(color_value) >> 16) & 255) / 255
            green = ((int(color_value) >> 8) & 255) / 255
            blue = (int(color_value) & 255) / 255
            return (red, green, blue)
        except Exception:
            return (0, 0, 0)

    def _build_edit_report(
        self,
        updated_text: str,
        instruction: str,
        changes: list[str],
        source_file: str,
        edits: list[DocumentEdit],
    ) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        edit_rows = [f"- {edit.label}: `{edit.old}` -> `{edit.new}` ({edit.scope})" for edit in edits]
        return "\n".join(
            [
                "## Document Edit Report",
                "",
                f"Source file: {Path(source_file).name}",
                f"Generated at: {timestamp}",
                "",
                "### Instruction",
                instruction.strip() or "No edit instruction was provided.",
                "",
                "### Applied Edits",
                *(edit_rows or ["- No concrete text edit could be inferred from the instruction."]),
                "",
                "### Changes",
                *(f"- {change}" for change in changes),
                "",
                "### Updated Text Extract",
                "",
                updated_text.strip(),
            ]
        )

    def _changes(self, edits: list[DocumentEdit]) -> list[str]:
        if not edits:
            return ["No concrete text replacement was applied. Provide an instruction like: replace 'old text' with 'new text'."]
        return [f"Update {edit.label} from {edit.old} to {edit.new}." for edit in edits]

    def _extract_summary(self, text: str) -> str:
        summary = self._section_text(text, "SUMMARY")
        return re.sub(r"\s+", " ", summary).strip()

    def _section_text(self, text: str, section_name: str) -> str:
        section = re.search(
            rf"^{re.escape(section_name)}\s*\n(?P<body>.*?)(?=\n[A-Z][A-Z &/+-]{{3,}}\s*\n|\Z)",
            text,
            flags=re.DOTALL | re.MULTILINE,
        )
        return section.group("body") if section else ""

    def _dedupe_edits(self, edits: list[DocumentEdit]) -> list[DocumentEdit]:
        output: list[DocumentEdit] = []
        seen: set[tuple[str, str, str]] = set()
        for edit in edits:
            key = (edit.old.lower(), edit.new.lower(), edit.scope, str(edit.replace_all))
            if edit.old and edit.new and edit.old.lower() != edit.new.lower() and key not in seen:
                output.append(edit)
                seen.add(key)
        return output

    def _clean_instruction_value(self, value: str) -> str:
        cleaned = re.sub(r"\s+", " ", value).strip(" .,:;\"'")
        cleaned = re.split(r"\s+\b(?:in|on)\s+the\s+(?:summary|profile|resume|pdf|document)\b", cleaned, flags=re.IGNORECASE)[0]
        return cleaned

    def _normalize_field_value(self, field: str, value: str) -> str:
        if field == "experience":
            value = re.sub(r"\byrs?\b", "years", value, flags=re.IGNORECASE)
        return value

    def _looks_like_field_name(self, value: str) -> bool:
        normalized = re.sub(r"^(?:the|a|an)\s+", "", value.strip().lower())
        return normalized in {"experience", "email", "phone", "mobile", "contact number", "title", "headline", "role", "summary", "profile"}

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
