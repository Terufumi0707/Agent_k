from __future__ import annotations

from app.models.domain_entities import Entry
from app.domain.policies import find_duplicate_work_types


def validate_entry(entry: Entry) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    if not entry.entry_id:
        issues.append({"field": "entry_id", "reason": "entry_id_required"})

    duplicates = find_duplicate_work_types(entry.constructions)
    if duplicates:
        issues.append(
            {
                "field": "constructions",
                "reason": "duplicate_work_type",
                "detail": ",".join(sorted(duplicates)),
            }
        )

    return issues
