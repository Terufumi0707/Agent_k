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
        # Controller/テストからの呼び出し形を統一的に扱うため、
        # 文字列・辞書・Pydanticモデルのいずれでも受け取れるようにしている。
        n_number = request if isinstance(request, str) else request
        if isinstance(n_number, dict):
            data = n_number
        elif isinstance(n_number, LookupByNNumberRequest):
            data = {"n_number": n_number.n_number}
        else:
            data = {"n_number": n_number}

        try:
            # 下位層へ渡す前にここでフォーマット検証し、
            # 不正入力をドメイン例外へマッピングする。
            validated = LookupByNNumberRequest.model_validate(data)
        except ValidationError as exc:
            raise InvalidIdentifierError(str(exc)) from exc

        return self._repository.find_by_n_number(validated.n_number)

    def get_by_web_entry_id(
        self, request: LookupByWebEntryIdRequest | dict[str, str] | str
    ) -> OrderRecord:
        # N番号検索と同様に、入力の受け口を一箇所に集約している。
        web_entry_id = request if isinstance(request, str) else request
        if isinstance(web_entry_id, dict):
            data = web_entry_id
        elif isinstance(web_entry_id, LookupByWebEntryIdRequest):
            data = {"web_entry_id": web_entry_id.web_entry_id}
        else:
            data = {"web_entry_id": web_entry_id}

        try:
            # バリデーション失敗時はValidationErrorをそのまま返さず、
            # API層で扱いやすい独自例外に変換する。
            validated = LookupByWebEntryIdRequest.model_validate(data)
        except ValidationError as exc:
            raise InvalidIdentifierError(str(exc)) from exc

        return self._repository.find_by_web_entry_id(validated.web_entry_id)
