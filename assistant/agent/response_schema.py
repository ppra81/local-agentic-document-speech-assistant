from __future__ import annotations

from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    success: bool
    answer: str
    summary: str = ""
    fields: dict = Field(default_factory=dict)
    citations: list[dict] = Field(default_factory=list)
    plan: dict = Field(default_factory=dict)
    report: dict = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)

