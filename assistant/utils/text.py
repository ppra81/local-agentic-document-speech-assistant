from __future__ import annotations

import re
from collections import Counter


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9₹$€£.\-]+", text.lower())


def keyword_score(query: str, text: str) -> float:
    q = Counter(tokenize(query))
    t = Counter(tokenize(text))
    if not q:
        return 0.0
    overlap = sum(min(count, t.get(term, 0)) for term, count in q.items())
    return overlap / max(sum(q.values()), 1)

