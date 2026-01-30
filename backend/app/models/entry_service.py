from __future__ import annotations

from app.models.domain_entities import Entry
from app.models.entry_repository import EntryRepository


class EntryService:
    def __init__(self, repository: EntryRepository) -> None:
        self._repository = repository

    def register_entry(self, entry: Entry) -> Entry:
        return self._repository.save(entry)

    def fetch_entry(self, entry_id: str) -> Entry | None:
        return self._repository.get(entry_id)
