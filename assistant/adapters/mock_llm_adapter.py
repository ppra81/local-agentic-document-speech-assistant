from __future__ import annotations

from typing import Any

from assistant.adapters.local_rule_based_adapter import LocalRuleBasedAdapter


class MockLLMAdapter(LocalRuleBasedAdapter):
    name = "mock_llm"
    task = "llm"

    def predict(self, input_data: dict[str, Any]) -> dict[str, Any]:
        return self.summarize_or_answer(input_data)

