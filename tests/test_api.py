from fastapi.testclient import TestClient
from pathlib import Path

from assistant.api.app import app


def test_api_health_endpoint_works():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_audio_transcribe_upload_endpoint_accepts_text_transcript():
    response = TestClient(app).post(
        "/audio/transcribe-upload",
        files={"file": ("instruction.txt", b"Update resume for agentic AI and RAG.", "text/plain")},
    )
    assert response.status_code == 200
    assert "agentic AI" in response.json()["transcript"]


def test_document_upload_endpoint_saves_file_and_extracts_text():
    response = TestClient(app).post(
        "/documents/upload",
        files={"file": ("resume.txt", b"SUMMARY\nData Scientist with 3+ years.\n", "text/plain")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert Path(payload["file_path"]).exists()
    assert "3+ years" in payload["text"]


def test_report_file_download_route_serves_report_file():
    client = TestClient(app)
    report_path = client.post(
        "/agent/ask",
        json={
            "request": "Read this resume, update the resume as per the recording, evaluate quality, and generate a report.",
            "file_path": "resume.pdf",
            "text": "Praneeth Reddy\nData Scientist\nSUMMARY\nML researcher.\nTECHNICAL SKILLS\nPython, PyTorch\nPROFESSIONAL EXPERIENCE\nProject Associate\nEDUCATION\nB.E.",
            "audio_file_path": "recording.m4a",
            "audio_text": "Update resume for agentic AI and RAG.",
        },
    ).json()["report"]["report"]["final_answer"]["updated_resume_pdf_path"]
    filename = report_path.replace("\\", "/").split("/")[-1]
    response = client.get(f"/reports/file/{filename}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
