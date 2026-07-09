from __future__ import annotations

from assistant.config import settings
from assistant.storage.local_store import JsonStore


document_store = JsonStore(settings.data_dir / "documents.json")

