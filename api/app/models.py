import re
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

N_NUMBER_PATTERN = re.compile(r"^N[0-9]{9}$")
WEB_ENTRY_ID_PATTERN = re.compile(r"^UN[0-9]{10}$")


class OrderInfo(BaseModel):
    main_a_number: str
    backup_a_number: Optional[str] = None
    main_work_types: List[str]
    main_work_date: List[Optional[str]] = Field(default_factory=list)
    backup_work_types: List[str]
    backup_work_date: List[Optional[str]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_work_dates(self) -> "OrderInfo":
        if len(self.main_work_date) != len(self.main_work_types):
            raise ValueError("main_work_date length must match main_work_types length")
        if len(self.backup_work_date) != len(self.backup_work_types):
            raise ValueError("backup_work_date length must match backup_work_types length")
        return self


class LookupByNNumberRequest(BaseModel):
    n_number: str

    @model_validator(mode="after")
    def validate_n_number(self) -> "LookupByNNumberRequest":
        if not N_NUMBER_PATTERN.match(self.n_number):
            raise ValueError("n_number の形式が不正です")
        return self


class LookupByWebEntryIdRequest(BaseModel):
    web_entry_id: str

    @model_validator(mode="after")
    def validate_web_entry_id(self) -> "LookupByWebEntryIdRequest":
        if not WEB_ENTRY_ID_PATTERN.match(self.web_entry_id):
            raise ValueError("web_entry_id の形式が不正です")
        return self


class IdentifiersResponse(BaseModel):
    n_number: str
    web_entry_id: str


class OrderStatusResponse(BaseModel):
    status: str
    last_updated: str


class ScheduledResponse(BaseModel):
    date: str
    time_slot: str


class ConstructionItemResponse(BaseModel):
    construction_item_id: str
    normalized_type: str
    overview: str
    scheduled: ScheduledResponse


class OrderLookupResponse(BaseModel):
    identifiers: IdentifiersResponse
    order_status: OrderStatusResponse
    construction: list[ConstructionItemResponse]


class ErrorDetail(BaseModel):
    code: str
    message: str
    trace_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
