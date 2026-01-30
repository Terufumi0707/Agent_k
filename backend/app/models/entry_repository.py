from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.models.construction_model import ConstructionModel
from app.models.domain_entities import Construction, Entry
from app.models.domain_value_objects import WorkType
from app.models.entry_model import EntryModel


class EntryRepository(Protocol):
    def save(self, entry: Entry) -> Entry:
        raise NotImplementedError

    def get(self, entry_id: str) -> Entry | None:
        raise NotImplementedError


@dataclass
class InMemoryEntryRepository:
    _entries: dict[str, EntryModel]
    _constructions: list[ConstructionModel]
    _next_id: int = 1

    def __init__(self) -> None:
        self._entries = {}
        self._constructions = []
        self._next_id = 1

    def save(self, entry: Entry) -> Entry:
        entry_model = self._to_entry_model(entry)
        self._entries[entry.entry_id] = entry_model
        self._constructions = [
            construction
            for construction in self._constructions
            if construction.entry_id != entry.entry_id
        ]
        self._constructions.extend(self._to_construction_models(entry))
        return self.get(entry.entry_id) or entry

    def get(self, entry_id: str) -> Entry | None:
        entry_model = self._entries.get(entry_id)
        if not entry_model:
            return None
        constructions = [
            construction
            for construction in self._constructions
            if construction.entry_id == entry_id
        ]
        return self._to_domain(entry_model, constructions)

    def _to_entry_model(self, entry: Entry) -> EntryModel:
        now = datetime.utcnow()
        existing = self._entries.get(entry.entry_id)
        if existing:
            return EntryModel(
                id=existing.id,
                entry_id=entry.entry_id,
                created_at=existing.created_at,
                updated_at=now,
            )
        entry_model = EntryModel(
            id=self._next_id,
            entry_id=entry.entry_id,
            created_at=now,
            updated_at=now,
        )
        self._next_id += 1
        return entry_model

    def _to_construction_models(self, entry: Entry) -> list[ConstructionModel]:
        return [
            ConstructionModel(
                id=index + 1,
                entry_id=entry.entry_id,
                work_type=construction.work_type.value,
                work_date=construction.work_date,
            )
            for index, construction in enumerate(entry.constructions)
        ]

    def _to_domain(
        self, entry_model: EntryModel, constructions: list[ConstructionModel]
    ) -> Entry:
        domain_constructions = [
            Construction(
                work_type=WorkType(construction.work_type),
                work_date=construction.work_date,
            )
            for construction in constructions
        ]
        return Entry(entry_id=entry_model.entry_id, constructions=domain_constructions)
