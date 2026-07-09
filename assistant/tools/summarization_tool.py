from __future__ import annotations

from assistant.adapters.local_rule_based_adapter import LocalRuleBasedAdapter
from assistant.tools.base import AssistantTool


class SummarizeDocumentTool(AssistantTool):
    name = "tool_summarize_document"
    description = "Create a local rule-based summary, answer, and field extraction."
    input_schema = {"text": "str", "request": "str", "chunks": "list optional"}
    output_schema = {"summary": "str", "answer": "str", "fields": "dict"}

    def __init__(self) -> None:
        self.adapter = LocalRuleBasedAdapter()

    def run(self, input_data: dict) -> dict:
        return self.adapter.predict(input_data)

