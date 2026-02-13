from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter

from app.domain.order import MultipleMatchesError, NotFoundError, OrderRecord, RepositoryUnavailableError
from app.models import (
    ConstructionItemResponse,
    ErrorDetail,
    ErrorResponse,
    IdentifiersResponse,
    OrderLookupResponse,
    OrderStatusResponse,
    ScheduledResponse,
)
from app.services.order_lookup_service import InvalidIdentifierError, OrderLookupService

router = APIRouter()


class ApiError(Exception):
    def __init__(self, status_code: int, payload: ErrorResponse) -> None:
        self.status_code = status_code
        self.payload = payload


def _format_order_response(order: OrderRecord) -> OrderLookupResponse:
    # ドメインのOrderRecordをAPIレスポンス契約に変換する。
    return OrderLookupResponse(
        identifiers=IdentifiersResponse(n_number=order.n_number, web_entry_id=order.web_entry_id),
        order_status=OrderStatusResponse(status=order.status, last_updated=order.last_updated.isoformat()),
        construction=[
            ConstructionItemResponse(
                construction_item_id=item.construction_item_id,
                normalized_type=item.normalized_type,
                overview=item.overview,
                scheduled=ScheduledResponse(date=item.scheduled_date, time_slot=item.scheduled_time_slot),
            )
            for item in order.construction
        ],
    )


def _raise_error(status_code: int, code: str, message: str) -> None:
    # 追跡しやすいようにtrace_idを都度採番して統一エラー形式で返す。
    trace_id = str(uuid4())
    raise ApiError(
        status_code=status_code,
        payload=ErrorResponse(error=ErrorDetail(code=code, message=message, trace_id=trace_id)),
    )


def _lookup_n(service: OrderLookupService, n_number: str) -> OrderLookupResponse:
    # サービス層の例外をHTTPエラーへ変換する責務をController層に寄せる。
    try:
        return _format_order_response(service.get_by_n_number(n_number))
    except InvalidIdentifierError:
        _raise_error(400, "INVALID_IDENTIFIER", "n_number の形式が不正です")
    except NotFoundError:
        _raise_error(404, "NOT_FOUND", "対象のオーダーが見つかりませんでした")
    except MultipleMatchesError:
        _raise_error(409, "MULTIPLE_MATCHES", "N番号に複数該当があります。WebエントリIDで指定してください")
    except RepositoryUnavailableError:
        _raise_error(503, "SERVICE_UNAVAILABLE", "下流システムが利用できません")


def _lookup_web_entry(service: OrderLookupService, web_entry_id: str) -> OrderLookupResponse:
    # web_entry_id検索の例外マッピング（N番号検索と同じ方針）。
    try:
        return _format_order_response(service.get_by_web_entry_id(web_entry_id))
    except InvalidIdentifierError:
        _raise_error(400, "INVALID_IDENTIFIER", "web_entry_id の形式が不正です")
    except NotFoundError:
        _raise_error(404, "NOT_FOUND", "対象のオーダーが見つかりませんでした")
    except RepositoryUnavailableError:
        _raise_error(503, "SERVICE_UNAVAILABLE", "下流システムが利用できません")


def bind_routes(service: OrderLookupService) -> APIRouter:
    # DIされたserviceをクロージャで保持し、ルータ定義と実処理を分離する。
    @router.get(
        "/v1/orders/by-n-number/{n_number}",
        response_model=OrderLookupResponse,
        responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    )
    def get_order_n_number(n_number: str) -> OrderLookupResponse:
        return _lookup_n(service, n_number)

    @router.get(
        "/v1/orders/{web_entry_id}",
        response_model=OrderLookupResponse,
        responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    )
    def get_order_webEntry(web_entry_id: str) -> OrderLookupResponse:
        return _lookup_web_entry(service, web_entry_id)

    return router
