from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

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


@router.get("/file/{filename}")
def download_report_file(filename: str) -> FileResponse:
    safe_name = Path(filename).name
    path = settings.reports_dir / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Report file not found")
    media_type = "application/pdf" if path.suffix.lower() == ".pdf" else "text/markdown" if path.suffix.lower() == ".md" else "application/json"
    return FileResponse(path, media_type=media_type, filename=safe_name)
