from __future__ import annotations

from assistant.agent.executor import AgentExecutor


def run_agent(request: str, file_path: str | None = None) -> dict:
    return AgentExecutor().run(request, file_path).model_dump()

