from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.order import (
    MultipleMatchesError,
    NotFoundError,
    OrderRecord,
    RepositoryUnavailableError,
    ScheduledConstruction,
)


class OrderRepository(Protocol):
    def find_by_n_number(self, n_number: str) -> OrderRecord:
        ...

    def find_by_web_entry_id(self, web_entry_id: str) -> OrderRecord:
        ...


class InMemoryOrderRepository:
    def __init__(self) -> None:
        self._orders = [
            OrderRecord(
                n_number="N123456789",
                web_entry_id="UN1234567890",
                status="CONFIRMED",
                last_updated=datetime.fromisoformat("2026-02-01T09:00:00+09:00"),
                construction=[
                    ScheduledConstruction(
                        construction_item_id="CI-0001",
                        normalized_type="切替工事",
                        overview="回線切替工事",
                        scheduled_date="2026-02-01",
                        scheduled_time_slot="09:00～12:00",
                    ),
                    ScheduledConstruction(
                        construction_item_id="CI-0002",
                        normalized_type="宅内工事",
                        overview="宅内工事",
                        scheduled_date="2026-02-08",
                        scheduled_time_slot="13:00～17:00",
                    ),
                ],
            ),
            OrderRecord(
                n_number="N000000002",
                web_entry_id="UN0000000002",
                status="CONFIRMED",
                last_updated=datetime.fromisoformat("2026-03-01T10:30:00+09:00"),
                construction=[
                    ScheduledConstruction(
                        construction_item_id="CI-1001",
                        normalized_type="切替工事",
                        overview="回線切替工事",
                        scheduled_date="2026-03-05",
                        scheduled_time_slot="09:00～12:00",
                    )
                ],
            ),
            OrderRecord(
                n_number="N222222222",
                web_entry_id="UN2222222222",
                status="CONFIRMED",
                last_updated=datetime.fromisoformat("2026-04-01T10:00:00+09:00"),
                construction=[
                    ScheduledConstruction(
                        construction_item_id="CI-2001",
                        normalized_type="宅内工事",
                        overview="宅内工事",
                        scheduled_date="2026-04-10",
                        scheduled_time_slot="13:00～17:00",
                    )
                ],
            ),
            OrderRecord(
                n_number="N222222222",
                web_entry_id="UN2222222223",
                status="CONFIRMED",
                last_updated=datetime.fromisoformat("2026-04-02T10:00:00+09:00"),
                construction=[
                    ScheduledConstruction(
                        construction_item_id="CI-2002",
                        normalized_type="切替工事",
                        overview="回線切替工事",
                        scheduled_date="2026-04-15",
                        scheduled_time_slot="09:00～12:00",
                    )
                ],
            ),
        ]

    def find_by_n_number(self, n_number: str) -> OrderRecord:
        if n_number == "N999999999":
            raise RepositoryUnavailableError("downstream unavailable")

        matches = [order for order in self._orders if order.n_number == n_number]
        if not matches:
            raise NotFoundError("order not found")
        if len(matches) > 1:
            raise MultipleMatchesError("multiple orders matched")
        return matches[0]

    def find_by_web_entry_id(self, web_entry_id: str) -> OrderRecord:
        if web_entry_id == "UN9999999999":
            raise RepositoryUnavailableError("downstream unavailable")

        for order in self._orders:
            if order.web_entry_id == web_entry_id:
                return order
        raise NotFoundError("order not found")
