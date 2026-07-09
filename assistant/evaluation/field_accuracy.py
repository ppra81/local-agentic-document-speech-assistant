from __future__ import annotations


def field_exact_match(prediction: dict, reference: dict) -> dict:
    total = len(reference)
    matches = {key: str(prediction.get(key, "")).strip().lower() == str(value).strip().lower() for key, value in reference.items()}
    accuracy = sum(matches.values()) / total if total else 0.0
    return {"field_accuracy": accuracy, "field_exact_match": matches}

