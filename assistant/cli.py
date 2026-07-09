from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from assistant.agent.executor import AgentExecutor
from assistant.config import settings
from assistant.rag.chunker import chunk_text
from assistant.rag.retriever import Retriever
from assistant.tools.evaluation_tool import EvaluateOutputTool
from assistant.tools.report_tool import GenerateReportTool
from assistant.utils.files import read_json, read_text_file
from assistant.utils.ids import stable_file_id

app = typer.Typer(help="Local Agentic AI Assistant for Documents, Speech, OCR, RAG, and Evaluation")


def _echo_json(data: dict) -> None:
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    sys.stdout.buffer.write(payload.encode("utf-8"))


@app.command()
def ask(request: str, file: Optional[Path] = typer.Option(None, "--file")) -> None:
    result = AgentExecutor().run(request, str(file) if file else None)
    _echo_json(result.model_dump())


@app.command()
def ingest(file: Path) -> None:
    text = read_text_file(file)
    document_id = stable_file_id(file)
    chunks = chunk_text(text, document_id, str(file), settings.chunk_size, settings.chunk_overlap)
    Retriever().index(document_id, chunks)
    _echo_json({"document_id": document_id, "chunks": len(chunks)})


@app.command()
def search(query: str, top_k: int = 5) -> None:
    _echo_json({"results": Retriever().search(query, top_k)})


@app.command()
def report(file: Path, request: str = "Extract the important fields and summarize the document.") -> None:
    result = AgentExecutor().run(f"{request} Generate a report.", str(file))
    _echo_json(result.report)


@app.command()
def evaluate(prediction: Path, reference: Path) -> None:
    output = EvaluateOutputTool().run({"prediction": read_json(prediction), "reference": read_json(reference)})
    _echo_json(output)


@app.command("api")
def api(host: str = "127.0.0.1", port: int = 8000) -> None:
    subprocess.run([sys.executable, "-m", "uvicorn", "assistant.api.app:app", "--host", host, "--port", str(port)], check=False)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
