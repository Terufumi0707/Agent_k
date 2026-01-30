from __future__ import annotations

from collections import Counter

from app.models.domain_entities import Construction


def find_duplicate_work_types(constructions: list[Construction]) -> list[str]:
    counts = Counter(construction.work_type.normalized() for construction in constructions)
    return [work_type for work_type, count in counts.items() if count > 1]
