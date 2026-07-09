from __future__ import annotations

from fastapi import APIRouter

from assistant.agent.executor import AgentExecutor
from assistant.api.schemas import AgentAskRequest

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/ask")
def ask_agent(payload: AgentAskRequest) -> dict:
    return AgentExecutor().run(
        payload.request,
        payload.file_path,
        payload.reference,
        payload.text,
        payload.audio_file_path,
        payload.audio_text,
    ).model_dump()
