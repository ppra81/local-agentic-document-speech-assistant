from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AssistantTool(ABC):
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]

    @abstractmethod
    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, AssistantTool] = {}

    def register(self, tool: AssistantTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> AssistantTool:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def list(self) -> list[dict[str, Any]]:
        return [{"name": t.name, "description": t.description, "input_schema": t.input_schema, "output_schema": t.output_schema} for t in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools.keys())

