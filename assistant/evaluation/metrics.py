from __future__ import annotations


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def error_rate(prediction: str, reference: str, unit: str = "char") -> float:
    if unit == "word":
        p = prediction.split()
        r = reference.split()
        return levenshtein(" ".join(p), " ".join(r)) / max(len(" ".join(r)), 1)
    return levenshtein(prediction, reference) / max(len(reference), 1)

