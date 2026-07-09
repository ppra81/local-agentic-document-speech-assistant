from fastapi.testclient import TestClient

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
