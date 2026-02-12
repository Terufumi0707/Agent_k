from __future__ import annotations

from pydantic import ValidationError

from app.domain.order import OrderRecord
from app.models import LookupByNNumberRequest, LookupByWebEntryIdRequest
from app.repositories.order_repository import OrderRepository


class InvalidIdentifierError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class OrderLookupService:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def get_by_n_number(self, request: LookupByNNumberRequest | dict[str, str] | str) -> OrderRecord:
        n_number = request if isinstance(request, str) else request
        if isinstance(n_number, dict):
            data = n_number
        elif isinstance(n_number, LookupByNNumberRequest):
            data = {"n_number": n_number.n_number}
        else:
            data = {"n_number": n_number}

        try:
            validated = LookupByNNumberRequest.model_validate(data)
        except ValidationError as exc:
            raise InvalidIdentifierError(str(exc)) from exc

        return self._repository.find_by_n_number(validated.n_number)

    def get_by_web_entry_id(
        self, request: LookupByWebEntryIdRequest | dict[str, str] | str
    ) -> OrderRecord:
        web_entry_id = request if isinstance(request, str) else request
        if isinstance(web_entry_id, dict):
            data = web_entry_id
        elif isinstance(web_entry_id, LookupByWebEntryIdRequest):
            data = {"web_entry_id": web_entry_id.web_entry_id}
        else:
            data = {"web_entry_id": web_entry_id}

        try:
            validated = LookupByWebEntryIdRequest.model_validate(data)
        except ValidationError as exc:
            raise InvalidIdentifierError(str(exc)) from exc

        return self._repository.find_by_web_entry_id(validated.web_entry_id)
