from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class WorkChange(BaseModel):
    work_type: Optional[str] = None
    desired_date: Optional[str] = None


class WorkTypeConfidence(BaseModel):
    name: str
    confidence: Literal["high", "medium", "low"]


class WorkParseRequest(BaseModel):
    message: str


class WorkParseResponse(BaseModel):
    operation: Literal["change", "add", "delete", "confirm"]
    work_types: List[WorkTypeConfidence]
    date: str
    date_inferred: bool
    notes: str


class IntakeStartRequest(BaseModel):
    a_number: Optional[str] = None
    entry_id: Optional[str] = None
    work_changes: Optional[List[WorkChange]] = None
    fetch_current_order: bool = False
    message: Optional[str] = None


class IntakeNextRequest(BaseModel):
    session_id: str
    a_number: Optional[str] = None
    entry_id: Optional[str] = None
    work_changes: Optional[List[WorkChange]] = None
    fetch_current_order: Optional[bool] = None
    message: Optional[str] = None


class OrderInfo(BaseModel):
    main_a_number: str
    backup_a_number: Optional[str] = None
    main_work_types: List[str]
    main_work_date: Optional[str] = None
    backup_work_types: List[str]
    backup_work_date: Optional[str] = None


class IntakeState(BaseModel):
    session_id: str
    a_number: Optional[str] = None
    entry_id: Optional[str] = None
    work_changes: List[WorkChange] = Field(default_factory=list)
    fetch_current_order: bool = False
    order_info: Optional[OrderInfo] = None
    missing_fields: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    status: Literal["need_more_info", "completed", "invalid_request"] = "need_more_info"
    logs: List[str] = Field(default_factory=list)
    last_user_message: Optional[str] = None
    assistant_message: Optional[str] = None


class IntakeResponse(BaseModel):
    session_id: str
    status: Literal["need_more_info", "completed", "invalid_request"]
    message: str
    missing_fields: List[str]
    questions: List[str]
    order_info: Optional[OrderInfo] = None
    assistant_message: Optional[str] = None


class AutonomousStartRequest(BaseModel):
    message: Optional[str] = None


class AutonomousNextRequest(BaseModel):
    session_id: str
    message: str


class AutonomousResponse(BaseModel):
    session_id: str
    status: Literal["need_more_info", "completed", "invalid_request"]
    message: str
    question: Optional[str] = None
    result: Optional[Dict[str, object]] = None
