from __future__ import annotations

from pathlib import Path
from typing import Any

from assistant.agent.planner import AgentPlanner
from assistant.agent.response_schema import AgentResponse
from assistant.agent.state import AgentRunState
from assistant.rag.citations import citations_from_results
from assistant.tools import build_tool_registry
from assistant.tools.base import ToolRegistry


class AgentExecutor:
    def __init__(self, registry: ToolRegistry | None = None, planner: AgentPlanner | None = None) -> None:
        self.registry = registry or build_tool_registry()
        self.planner = planner or AgentPlanner()

    def run(
        self,
        user_request: str,
        file_path: str | None = None,
        reference: dict | None = None,
        input_text: str | None = None,
        audio_file_path: str | None = None,
        audio_text: str | None = None,
    ) -> AgentResponse:
        plan = self.planner.create_plan(user_request, file_path, audio_file_path)
        state = AgentRunState(user_request=user_request, file_path=file_path, plan=plan)
        context: dict[str, Any] = {
            "request": user_request,
            "file_path": file_path,
            "audio_file_path": audio_file_path,
            "audio_text": audio_text,
            "text": input_text or "",
            "document_text": input_text or "",
            "query": user_request,
            "reference": reference or {},
        }
        for step in plan.steps:
            try:
                if step.tool == "tool_generate_report":
                    state.tools_used.append(step.tool)
                    state.intermediate_outputs[step.tool] = {"status": "deferred_until_final_payload_ready"}
                    continue
                tool = self.registry.get(step.tool)
                output = self._run_tool(tool.name, context)
                state.intermediate_outputs[tool.name] = output
                state.tools_used.append(tool.name)
                self._merge_context(tool.name, output, context)
            except Exception as exc:
                state.errors.append(f"{step.tool}: {exc}")
        final = context.get("final_answer", {})
        citations = citations_from_results(context.get("retrieval_results", []))
        run_payload = {
            "input_file": file_path,
            "user_request": user_request,
            "agent_plan": plan.model_dump(),
            "tools_used": state.tools_used,
            "intermediate_outputs": state.intermediate_outputs,
            "retrieved_evidence": citations,
            "final_answer": final,
            "evaluation_metrics": context.get("evaluation_metrics", {}),
            "errors_or_warnings": state.errors,
        }
        report = self.registry.get("tool_generate_report").run({"run": run_payload})
        return AgentResponse(
            success=not state.errors,
            answer=final.get("answer") or "I could not find enough evidence in the uploaded document.",
            summary=final.get("summary", ""),
            fields=final.get("fields", {}),
            citations=citations,
            plan=plan.model_dump(),
            report=report,
            errors=state.errors,
        )

    def _run_tool(self, name: str, context: dict[str, Any]) -> dict[str, Any]:
        tool = self.registry.get(name)
        if name == "tool_evaluate_output":
            prediction = {
                "text": context.get("document_text") or context.get("text", ""),
                "transcript": context.get("transcript", ""),
                "fields": context.get("final_answer", {}).get("fields", {}),
                "summary": context.get("final_answer", {}).get("summary", ""),
                "source_text": context.get("document_text") or context.get("text", ""),
                "retrieval_results": context.get("retrieval_results", []),
            }
            return tool.run({"prediction": prediction, "reference": context.get("reference", {})})
        if name == "tool_transcribe_audio":
            return tool.run({"file_path": context.get("audio_file_path") or context.get("file_path"), "text": context.get("audio_text")})
        if name == "tool_update_resume_from_instruction":
            return tool.run(
                {
                    "resume_text": context.get("document_text") or context.get("text", ""),
                    "instruction": context.get("transcript") or context.get("request", ""),
                    "source_file": context.get("file_path"),
                }
            )
        if name == "tool_generate_report":
            return tool.run({"run": {}})
        return tool.run(context)

    def _merge_context(self, name: str, output: dict[str, Any], context: dict[str, Any]) -> None:
        if "text" in output:
            context["text"] = output["text"]
            context["document_text"] = output["text"]
        if "transcript" in output:
            context["transcript"] = output["transcript"]
        if "document_id" in output:
            context["document_id"] = output["document_id"]
        if "chunks" in output:
            context["chunks"] = output["chunks"]
        if "results" in output:
            context["retrieval_results"] = output["results"]
        if name == "tool_summarize_document":
            context["final_answer"] = output
        if name == "tool_update_resume_from_instruction":
            current = context.get("final_answer", {})
            context["updated_resume"] = output
            context["final_answer"] = {
                **current,
                "answer": "Updated resume generated from the document and recording instruction.",
                "updated_resume_path": output.get("updated_resume_path"),
                "changes": output.get("changes", []),
                "fields": output.get("fields", current.get("fields", {})),
            }
        if name == "tool_evaluate_output":
            context["evaluation_metrics"] = output.get("metrics", {})
        if name == "tool_generate_report":
            context["report"] = output
