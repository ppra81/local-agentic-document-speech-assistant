from __future__ import annotations

from typing import Any

from assistant.adapters.base import ModelAdapter
from assistant.utils.text import tokenize


class MockEmbeddingAdapter(ModelAdapter):
    name = "mock_embedding"
    task = "embedding"

    def predict(self, input_data: dict[str, Any]) -> dict[str, Any]:
        tokens = tokenize(input_data.get("text", ""))
        vocab = sorted(set(tokens))[:64]
        vector = [float(tokens.count(term)) for term in vocab]
        return {"embedding": vector, "dimensions": len(vector), "adapter": self.name}

