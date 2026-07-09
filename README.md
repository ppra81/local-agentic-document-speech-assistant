# Local Agentic AI Assistant for Documents, Speech, OCR, and Evaluation

`local_agentic_document_speech_assistant` is a local-first portfolio project that connects document OCR, mock speech transcription, translation, RAG, evaluation, and report generation into one agentic workflow.

The first version requires no paid APIs and no heavy model downloads. Mock and rule-based adapters make the system runnable immediately, while typed interfaces keep real OCR, ASR, embedding, vector database, and LLM backends easy to plug in later.

## Why Agentic Local AI Matters

Many useful AI products are workflows, not single prompts. A production assistant must choose tools, preserve intermediate outputs, ground answers in sources, evaluate quality, and create artifacts that a user can inspect. This project demonstrates that pattern with a local, testable Python architecture.

## What Problem This Solves

The assistant accepts a request such as:

```text
Read this document, extract important fields, translate them to English, summarize the content, evaluate extraction quality, and generate a report.
```

It plans and executes tool calls for OCR, ASR, translation, chunking, retrieval, summarization, evaluation, and report generation.

## Architecture

- `assistant/agent`: planner, executor, state, and response schemas.
- `assistant/tools`: production-style tool registry and tool wrappers.
- `assistant/adapters`: mock/local model adapters with clean extension points.
- `assistant/rag`: chunking, keyword index, retrieval, and citations.
- `assistant/evaluation`: CER, WER, field accuracy, coverage, and retrieval metrics.
- `assistant/api`: FastAPI backend.
- `web`: simple local browser UI.
- `tests`: pytest coverage for CLI, API, tools, RAG, evaluation, and reports.

## Tool-Calling Workflow

The planner converts a user request into structured steps:

```json
{
  "goal": "Complete a local document, speech, retrieval, and reporting workflow",
  "steps": [
    {"tool": "tool_ocr_document", "reason": "The input may contain document text or image content."},
    {"tool": "tool_chunk_document", "reason": "The content should be split into searchable sections."},
    {"tool": "tool_search_document_chunks", "reason": "Relevant evidence should be retrieved from chunks."},
    {"tool": "tool_summarize_document", "reason": "The user asked for a summary, answer, or extracted fields."},
    {"tool": "tool_generate_report", "reason": "A persistent structured report is useful for this workflow."}
  ]
}
```

Every tool has `name`, `description`, `input_schema`, `output_schema`, and `run()`.

## RAG Workflow

Documents are read locally, split into overlapping chunks, stored in `.local_data/rag_index.json`, and searched with keyword scoring. Answers include citations with source file, chunk id, snippet, and confidence score. If evidence is insufficient, the assistant returns: `I could not find enough evidence in the uploaded document.`

## Evaluation Workflow

The evaluation tool supports OCR character error rate, ASR word error rate, ASR character error rate, field-level exact match, field-level accuracy, summary coverage mock score, and retrieval hit rate.

## Report Generation

Each agent run can generate JSON and Markdown reports under `reports/`. Reports include the input file, user request, plan, tools used, intermediate outputs, evidence, final answer, metrics, errors, and timestamp.

## CLI Usage

Install locally:

```bash
pip install -e ".[dev]"
```

Run:

```bash
local-agent ask "Summarize this document" --file examples/sample_invoice.txt
local-agent ingest --file examples/sample_invoice.txt
local-agent search "total amount"
local-agent report --file examples/sample_invoice.txt
local-agent evaluate --prediction reports/prediction.json --reference examples/reference.json
local-agent api
```

## API Usage

Start the server:

```bash
uvicorn assistant.api.app:app --reload
```

Endpoints:

- `GET /health`
- `POST /agent/ask`
- `POST /documents/ingest`
- `POST /audio/transcribe`
- `POST /documents/search`
- `POST /reports/generate`
- `POST /evaluate`
- `GET /reports/{report_id}`

Example:

```bash
curl -X POST http://127.0.0.1:8000/agent/ask \
  -H "Content-Type: application/json" \
  -d "{\"request\":\"Extract vendor, date, total and summarize. Generate a report.\",\"file_path\":\"examples/sample_invoice.txt\"}"
```

## Local Website Usage

Start the API, then open `web/index.html` in a browser. The page lets you choose workflows for full agent runs, document ingestion, search, mock ASR, and report generation.

## Docker

```bash
docker compose up --build
```

The API is exposed at `http://127.0.0.1:8000`.

## Testing

```bash
pytest
```

## Plugging In Real OCR Models

Use `TesseractOCRAdapter` in `assistant/adapters/tesseract_ocr_adapter.py` or add another adapter implementing `ModelAdapter.predict()`, then inject it into `OCRDocumentTool`. If the optional dependency is missing, the adapter returns: `Optional dependency not installed. Falling back to mock adapter.`

Good candidates: Tesseract, EasyOCR, PaddleOCR.

## Plugging In Real ASR Models

Use `WhisperASRAdapter` in `assistant/adapters/whisper_asr_adapter.py` or create another ASR adapter with the same interface as `MockASRAdapter`. Model loading is lazy so the API and CLI still start on machines without the dependency.

Good candidates: Whisper, faster-whisper, Vosk.

## Plugging In Real LLMs

Replace or extend `LocalRuleBasedAdapter` with a local LLM adapter. The executor already passes request, text, chunks, retrieved evidence, and reference data through the shared context.

Good candidates: llama.cpp, Ollama, vLLM, Transformers.

## Connecting To OCR, Speech, Evaluation, And AI API Projects

This project is designed as a unifying workflow layer. OCR projects can supply extracted text, speech projects can supply transcripts, evaluation projects can score outputs, and API platform projects can expose these capabilities as product endpoints.

## Recruiter-Ready Explanation

This repository shows practical agentic AI engineering beyond a notebook demo: tool planning, tool execution, local RAG, source grounding, structured outputs, evaluation metrics, report artifacts, CLI ergonomics, FastAPI endpoints, Docker support, and tests.

## Future Roadmap

- Add optional Tesseract and Whisper adapters.
- Add vector retrieval behind the existing retriever interface.
- Add local LLM support with structured JSON output validation.
- Add file upload handling in the FastAPI UI path.
- Add richer evaluation dashboards and HTML reports.
