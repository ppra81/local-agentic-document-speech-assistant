from __future__ import annotations

from assistant.config import settings
from assistant.storage.local_store import JsonStore


artifact_store = JsonStore(settings.data_dir / "artifacts.json")

