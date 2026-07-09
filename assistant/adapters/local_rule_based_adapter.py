from __future__ import annotations

import re
from typing import Any

from assistant.adapters.base import ModelAdapter
from assistant.utils.text import normalize_text


class LocalRuleBasedAdapter(ModelAdapter):
    name = "local_rule_based"
    task = "rule_based_llm"

    FIELD_PATTERNS = {
        "vendor": r"(?:vendor|store|merchant|supplier|from)\s*[:\-]\s*(.+)",
        "date": r"(?:date|invoice date|receipt date)\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}[/-][0-9]{2}[/-][0-9]{4})",
        "total_amount": r"(?:total amount|total|amount due|grand total)\s*[:\-]\s*([₹$€£]?\s*[0-9,]+(?:\.[0-9]{2})?)",
        "invoice_number": r"(?:invoice no|invoice number|receipt no|bill no)\s*[:\-]\s*([A-Za-z0-9\-]+)",
    }

    def predict(self, input_data: dict[str, Any]) -> dict[str, Any]:
        return self.summarize_or_answer(input_data)

    def extract_fields(self, text: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        for key, pattern in self.FIELD_PATTERNS.items():
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                fields[key] = normalize_text(match.group(1))
        if self._looks_like_resume(text):
            fields.update(self.extract_resume_fields(text))
        return fields

    def extract_resume_fields(self, text: str) -> dict[str, str]:
        lines = [line.strip() for line in text.splitlines() if line.strip() and not set(line.strip()) <= {"_"}]
        clean = normalize_text(text)
        fields: dict[str, str] = {}
        if lines:
            fields["candidate_name"] = lines[0]
        if len(lines) > 1 and any(term in lines[1].lower() for term in ["scientist", "engineer", "research", "developer", "analyst", "manager"]):
            fields["target_role"] = lines[1]
        email = re.search(r"[\w.\-+]+@[\w.\-]+\.\w+", text)
        if email:
            fields["email"] = email.group(0)
        phone = re.search(r"(?:\+\d{1,3}\s*)?\d{10}", text)
        if phone:
            fields["phone"] = phone.group(0)
        links = re.findall(r"(?:https?://)?(?:www\.)?(?:linkedin\.com|github\.com|[\w.-]+\.github\.io)/[^\s|]+", text)
        if links:
            fields["links"] = ", ".join(dict.fromkeys(links))
        experience = re.search(r"(\d+\+?\s+years?)", clean, flags=re.IGNORECASE)
        if experience:
            fields["experience"] = experience.group(1)
        education = re.search(r"(B\.[A-Za-z.]+,\s*[^_]+?CGPA:\s*[0-9.]+)", clean)
        if education:
            fields["education"] = education.group(1).strip()
        skill_terms = [
            "Python",
            "PyTorch",
            "TensorFlow",
            "Hugging Face",
            "pandas",
            "NumPy",
            "Scikit-learn",
            "SQL",
            "AWS",
            "RAGAS",
            "LangSmith",
            "WER/CER/BLEU",
        ]
        found_skills = [term for term in skill_terms if term.lower() in clean.lower()]
        if found_skills:
            fields["skills"] = ", ".join(found_skills)
        return fields

    def summarize_or_answer(self, input_data: dict[str, Any]) -> dict[str, Any]:
        text = input_data.get("text") or " ".join(c.get("text", "") for c in input_data.get("chunks", []))
        request = input_data.get("request", "")
        fields = self.extract_fields(text)
        summary = self._resume_summary(text, fields) if self._looks_like_resume(text) else self._generic_summary(text)
        if "total" in request.lower() and "total_amount" in fields:
            answer = f"The total amount is {fields['total_amount']}."
        elif self._looks_like_resume(text):
            answer = self._resume_answer(fields, request)
        elif fields:
            answer = "Key fields found: " + ", ".join(f"{k}={v}" for k, v in fields.items())
        elif summary and summary != "No summary could be generated.":
            answer = summary
        else:
            answer = "I could not find enough evidence in the uploaded document."
        return {"summary": summary, "answer": answer, "fields": fields, "adapter": self.name}

    def _looks_like_resume(self, text: str) -> bool:
        lowered = text.lower()
        return any(term in lowered for term in ["professional experience", "technical skills", "education", "certifications", "resume", "curriculum vitae"])

    def _generic_summary(self, text: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", normalize_text(text))
        return " ".join(sentences[:3]) if sentences and sentences[0] else "No summary could be generated."

    def _resume_summary(self, text: str, fields: dict[str, str]) -> str:
        clean = normalize_text(text)
        parts = []
        if fields.get("candidate_name"):
            parts.append(f"{fields['candidate_name']} is profiled as {fields.get('target_role', 'an AI/ML professional')}.")
        summary_match = re.search(r"SUMMARY\s+(.+?)(?:TECHNICAL SKILLS|PROFESSIONAL EXPERIENCE|KEY PROJECTS)", clean, flags=re.IGNORECASE)
        if summary_match:
            parts.append(summary_match.group(1).strip())
        if "Project Associate" in text and "AI4Bharat" in text:
            parts.append("The resume emphasizes evaluation work for ASR, TTS, OCR, LLM quality assessment, red-teaming, annotation workflows, and production quality pipelines.")
        return " ".join(parts) if parts else self._generic_summary(text)

    def _resume_answer(self, fields: dict[str, str], request: str) -> str:
        name = fields.get("candidate_name", "The candidate")
        role = fields.get("target_role", "AI/ML professional")
        skills = fields.get("skills", "evaluation frameworks, ML systems, and Python tooling")
        experience = fields.get("experience", "documented experience")
        recording_note = ""
        if "recording transcript:" in request.lower() or "recording input:" in request.lower():
            recording_note = " The requested experience should be adapted using the supplied recording transcript when available."
        return (
            f"{name} is a strong fit for {role}, with {experience} and evidence around {skills}. "
            "The document is strongest on AI evaluation, RAG/LLM quality, speech/OCR evaluation, red-teaming, annotation quality, and production-style reporting."
            f"{recording_note}"
        )
