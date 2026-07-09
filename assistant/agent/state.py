from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    tool: str
    reason: str


class AgentPlan(BaseModel):
    goal: str
    steps: list[PlanStep]


class AgentRunState(BaseModel):
    user_request: str
    file_path: str | None = None
    plan: AgentPlan
    intermediate_outputs: dict[str, Any] = Field(default_factory=dict)
    tools_used: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

