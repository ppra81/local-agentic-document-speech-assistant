from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from assistant.config import settings
from assistant.tools.base import AssistantTool
from assistant.utils.ids import new_id


class GenerateReportTool(AssistantTool):
    name = "tool_generate_report"
    description = "Generate JSON and Markdown reports for a completed agent run."
    input_schema = {"run": "dict"}
    output_schema = {"report_id": "str", "json_path": "str", "markdown_path": "str"}

    def run(self, input_data: dict) -> dict:
        report_id = input_data.get("report_id") or new_id("report")
        run = input_data.get("run", input_data)
        run["timestamp"] = run.get("timestamp") or datetime.now(timezone.utc).isoformat()
        run["report_id"] = report_id
        json_path = settings.reports_dir / f"{report_id}.json"
        md_path = settings.reports_dir / f"{report_id}.md"
        json_path.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
        md_path.write_text(self._markdown(run), encoding="utf-8")
        return {"report_id": report_id, "json_path": str(json_path), "markdown_path": str(md_path), "report": run}

    def _markdown(self, run: dict) -> str:
        tools = run.get("tools_used", [])
        fields = run.get("final_answer", {}).get("fields", {})
        evidence = run.get("retrieved_evidence", [])
        metrics = run.get("evaluation_metrics", {})
        lines = [
            "# Local Agentic Document + Speech Assistant Report",
            "",
            "## User Request",
            run.get("user_request", ""),
            "",
            "## Tools Used",
            *[f"{i}. {tool}" for i, tool in enumerate(tools, 1)],
            "",
            "## Extracted Fields",
        ]
        lines.extend([f"- {k}: {v}" for k, v in fields.items()] or ["- No structured fields extracted."])
        lines.extend(["", "## Summary", run.get("final_answer", {}).get("summary", ""), "", "## Evidence"])
        lines.extend([f"- Source: {e.get('source_file')} | Chunk: {e.get('chunk_id')} | Score: {e.get('confidence'):.2f} | Text: {e.get('matched_text_snippet')}" for e in evidence] or ["- No evidence retrieved."])
        lines.extend(["", "## Evaluation"])
        lines.extend([f"- {k}: {v}" for k, v in metrics.items()] or ["- No metrics calculated."])
        lines.extend(["", "## Notes", "This result was generated locally using mock adapters."])
        return "\n".join(lines) + "\n"

