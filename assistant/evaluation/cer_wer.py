from __future__ import annotations

from assistant.evaluation.metrics import error_rate


def character_error_rate(prediction: str, reference: str) -> float:
    return error_rate(prediction, reference, unit="char")


def word_error_rate(prediction: str, reference: str) -> float:
    p_words = prediction.split()
    r_words = reference.split()
    if not r_words:
        return 0.0
    # Lightweight first-version approximation using token set mismatch.
    mismatches = sum(1 for i, word in enumerate(r_words) if i >= len(p_words) or p_words[i] != word)
    mismatches += max(len(p_words) - len(r_words), 0)
    return mismatches / len(r_words)

