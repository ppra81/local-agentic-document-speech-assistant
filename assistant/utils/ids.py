from __future__ import annotations

import hashlib
import uuid
from pathlib import Path


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def stable_file_id(path: str | Path) -> str:
    p = Path(path)
    digest = hashlib.sha1(str(p.resolve()).encode("utf-8")).hexdigest()[:12]
    return f"doc_{digest}"

