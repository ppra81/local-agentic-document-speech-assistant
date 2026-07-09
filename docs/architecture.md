# Architecture

The project is organized around a local agent loop:

1. Planner converts the user request into tool steps.
2. Executor calls each tool and stores intermediate outputs.
3. RAG components chunk, index, search, and cite evidence.
4. Evaluation components score extraction, transcription, retrieval, and summaries.
5. Report generation writes Markdown and JSON artifacts.

The first version uses mock adapters to keep the system runnable without paid APIs or heavy downloads.

