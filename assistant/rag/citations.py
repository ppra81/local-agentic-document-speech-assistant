from __future__ import annotations


def citations_from_results(results: list[dict]) -> list[dict]:
    return [
        {
            "source_file": item.get("source_file"),
            "chunk_id": item.get("chunk_id"),
            "matched_text_snippet": item.get("snippet") or item.get("text", "")[:220],
            "confidence": item.get("score", 0.0),
        }
        for item in results
    ]

