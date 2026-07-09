from __future__ import annotations


def summary_coverage_score(summary: str, source_text: str) -> float:
    source_terms = {t.lower().strip(".,:;") for t in source_text.split() if len(t) > 3}
    summary_terms = {t.lower().strip(".,:;") for t in summary.split() if len(t) > 3}
    return len(summary_terms & source_terms) / max(len(summary_terms), 1)


def retrieval_hit_rate(results: list[dict], expected_terms: list[str]) -> float:
    haystack = " ".join(item.get("text", "") for item in results).lower()
    if not expected_terms:
        return 0.0
    return sum(1 for term in expected_terms if term.lower() in haystack) / len(expected_terms)

