from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from assistant.agent.executor import AgentExecutor
from assistant.api.schemas import ReportRequest
from assistant.config import settings

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate")
def generate_report(payload: ReportRequest) -> dict:
    result = AgentExecutor().run(
        f"{payload.request} Generate a report.",
        payload.file_path,
        input_text=payload.text,
        audio_file_path=payload.audio_file_path,
        audio_text=payload.audio_text,
    )
    return result.report


@router.get("/{report_id}")
def get_report(report_id: str) -> dict:
    path = settings.reports_dir / f"{report_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return {"report_id": report_id, "json": path.read_text(encoding="utf-8"), "markdown_path": str(settings.reports_dir / f"{report_id}.md")}
