from __future__ import annotations

from pathlib import Path

from assistant.config import settings


def ensure_storage() -> None:
    for path in [settings.data_dir, settings.reports_dir, settings.data_dir / "artifacts", settings.data_dir / "documents"]:
        Path(path).mkdir(parents=True, exist_ok=True)

