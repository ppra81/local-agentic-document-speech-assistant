from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    project_root: Path = Path(__file__).resolve().parents[1]
    data_dir: Path = project_root / ".local_data"
    reports_dir: Path = project_root / "reports"
    chunk_size: int = 550
    chunk_overlap: int = 80


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)

