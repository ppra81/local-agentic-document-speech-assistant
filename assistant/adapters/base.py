from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ModelAdapter(ABC):
    name: str
    task: str

    @abstractmethod
    def predict(self, input_data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class OptionalDependencyAdapter(ModelAdapter):
    dependency_name: str = ""

    def dependency_available(self) -> bool:
        try:
            __import__(self.dependency_name)
            return True
        except Exception:
            return False

    def fallback_message(self) -> str:
        return "Optional dependency not installed. Falling back to mock adapter."

