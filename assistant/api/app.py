from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from assistant.api.routes_agent import router as agent_router
from assistant.api.routes_audio import router as audio_router
from assistant.api.routes_documents import router as documents_router
from assistant.api.routes_reports import router as reports_router
from assistant.api.schemas import EvaluateRequest
from assistant.tools.evaluation_tool import EvaluateOutputTool

app = FastAPI(title="Local Agentic Document Speech Assistant", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = Path(__file__).resolve().parents[2] / "web"
if WEB_DIR.exists():
    app.mount("/ui", StaticFiles(directory=WEB_DIR, html=True), name="ui")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "local_first": True}


@app.get("/")
def root() -> dict:
    return {
        "name": "Local Agentic Document Speech Assistant",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "website": "/ui",
    }


@app.post("/evaluate")
def evaluate(payload: EvaluateRequest) -> dict:
    return EvaluateOutputTool().run({"prediction": payload.prediction, "reference": payload.reference})


app.include_router(agent_router)
app.include_router(documents_router)
app.include_router(audio_router)
app.include_router(reports_router)
