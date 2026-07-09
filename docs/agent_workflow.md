# Agent Workflow

The planner is rule-based in version one. It detects whether the input looks like audio or document content, then adds tools for translation, chunking, retrieval, summarization, evaluation, and reporting based on request intent.

The executor is responsible for graceful failure handling. Tool errors are collected in the final response and report instead of crashing the whole run.

