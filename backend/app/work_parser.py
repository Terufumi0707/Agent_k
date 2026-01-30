from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

from app.llm_client import parse_work_message_with_gemini
from app.llm_prompts import gemini_work_parse_prompt

WORK_TYPE_ALIASES: Dict[str, List[str]] = {
    "現地調査": ["現地調査", "現調"],
    "付帯工事": ["付帯工事", "付帯"],
    "アクセス工事": ["アクセス工事", "アクセス"],
    "導通工事": ["導通工事", "導通"],
    "事前配線": ["事前配線"],
    "宅内工事": ["宅内工事", "宅内"],
    "端末工事": ["端末工事", "端末"],
    "切替工事": ["切替工事", "切替", "切り替え", "切り替え工事"],
    "端末撤去": ["端末撤去"],
    "コム撤去": ["コム撤去"],
    "地域撤去": ["地域撤去"],
    "ケーブル撤去": ["ケーブル撤去"],
    "PD撤去": ["PD撤去"],
    "DF現調": ["DF現調"],
    "開通日": ["開通日", "開通"],
}

REMOVAL_TYPES = ["端末撤去", "コム撤去", "地域撤去", "ケーブル撤去", "PD撤去"]

OPERATION_KEYWORDS = {
    "change": ["変更", "変え", "修正", "変更したい", "変更した", "更新"],
    "add": ["追加", "入れ", "加え", "増や"],
    "delete": ["削除", "取り消し", "キャンセル", "消し", "外し"],
    "confirm": ["確認", "教えて", "見たい", "チェック"],
}


ALLOWED_OPERATIONS = {"change", "add", "delete", "confirm"}


@dataclass
class DateResult:
    value: str
    inferred: bool
    note: Optional[str] = None


def parse_work_request(
    message: str,
    today: Optional[date] = None,
    use_llm: bool = True,
) -> Dict[str, object]:
    if not message:
        message = ""
    base_date = today or date.today()
    llm_result: Dict[str, object] = {}
    if use_llm:
        prompt = gemini_work_parse_prompt(message)
        llm_result = parse_work_message_with_gemini(prompt)

    return _merge_with_fallback(message, base_date, llm_result)


def _merge_with_fallback(message: str, base_date: date, llm_result: Dict[str, object]) -> Dict[str, object]:
    operation, operation_note = _normalize_operation(llm_result.get("operation"), message)

    work_types, work_type_note = _normalize_work_types(llm_result.get("work_types"), message)
    work_type_note = _work_type_notes(work_types, message, work_type_note)

    date_value, date_inferred, date_note = _normalize_date(llm_result, message, base_date)

    notes = [note for note in [operation_note, work_type_note, date_note, llm_result.get("notes")] if note]
    note_text = " / ".join([str(note) for note in notes if str(note).strip()]) if notes else ""

    return {
        "operation": operation,
        "work_types": work_types,
        "date": date_value,
        "date_inferred": date_inferred,
        "notes": note_text,
    }


def _normalize_operation(operation: Optional[object], message: str) -> Tuple[str, Optional[str]]:
    if isinstance(operation, str) and operation in ALLOWED_OPERATIONS:
        return operation, None
    return extract_operation(message)


def _normalize_work_types(
    raw: Optional[object],
    message: str,
) -> Tuple[List[Dict[str, str]], Optional[str]]:
    normalized: List[Dict[str, str]] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            confidence = item.get("confidence")
            if name in WORK_TYPE_ALIASES and confidence in {"high", "medium", "low"}:
                normalized.append({"name": name, "confidence": confidence})
    if normalized:
        return normalized, None
    return extract_work_types(message)


def _work_type_notes(
    work_types: List[Dict[str, str]],
    message: str,
    fallback_note: Optional[str],
) -> Optional[str]:
    notes: List[str] = []
    if fallback_note:
        notes.append(fallback_note)
    if "撤去" in message and not any(item["name"] in REMOVAL_TYPES for item in work_types):
        for name in REMOVAL_TYPES:
            work_types.append({"name": name, "confidence": "low"})
        notes.append("撤去の種別が特定できないため撤去系候補を列挙")
    if not work_types:
        for name in WORK_TYPE_ALIASES.keys():
            work_types.append({"name": name, "confidence": "low"})
        notes.append("工事種別が明示されていないため全候補を提示")
    return " / ".join(notes) if notes else None


def _normalize_date(
    llm_result: Dict[str, object],
    message: str,
    base_date: date,
) -> Tuple[str, bool, Optional[str]]:
    date_value = llm_result.get("date")
    date_inferred = llm_result.get("date_inferred")
    if isinstance(date_value, str) and _is_iso_date(date_value):
        inferred = bool(date_inferred) if isinstance(date_inferred, bool) else False
        return date_value, inferred, None
    date_result = extract_date(message, base_date)
    return date_result.value, date_result.inferred, date_result.note


def extract_operation(message: str) -> Tuple[str, Optional[str]]:
    for operation, keywords in OPERATION_KEYWORDS.items():
        if any(keyword in message for keyword in keywords):
            return operation, None
    return "change", "操作内容が明示されていないため変更として推定"


def extract_work_types(message: str) -> Tuple[List[Dict[str, str]], Optional[str]]:
    found: List[Dict[str, str]] = []
    matched_names = set()
    for name, aliases in WORK_TYPE_ALIASES.items():
        if any(alias in message for alias in aliases):
            found.append({"name": name, "confidence": "high"})
            matched_names.add(name)

    notes: List[str] = []
    if "撤去" in message and not any(name in matched_names for name in REMOVAL_TYPES):
        for name in REMOVAL_TYPES:
            found.append({"name": name, "confidence": "low"})
        notes.append("撤去の種別が特定できないため撤去系候補を列挙")

    if not found:
        for name in WORK_TYPE_ALIASES.keys():
            found.append({"name": name, "confidence": "low"})
        notes.append("工事種別が明示されていないため全候補を提示")

    return found, " / ".join(notes) if notes else None


def _is_iso_date(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def extract_date(message: str, base_date: date) -> DateResult:
    explicit = _match_explicit_date(message)
    if explicit:
        return DateResult(explicit, inferred=False)

    relative = _match_relative_date(message, base_date)
    if relative:
        return relative

    month_day = _match_month_day(message, base_date)
    if month_day:
        return month_day

    day_only = _match_day_only(message, base_date)
    if day_only:
        return day_only

    fallback = base_date.isoformat()
    return DateResult(fallback, inferred=True, note="日付が明示されていないため本日を仮置き")


def _match_explicit_date(message: str) -> Optional[str]:
    patterns = [
        r"(?P<year>\d{4})[/-](?P<month>\d{1,2})[/-](?P<day>\d{1,2})",
        r"(?P<year>\d{4})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if not match:
            continue
        return _format_date(int(match.group("year")), int(match.group("month")), int(match.group("day")))
    return None


def _match_relative_date(message: str, base_date: date) -> Optional[DateResult]:
    relative_map = {"今月": 0, "来月": 1, "再来月": 2}
    for label, offset in relative_map.items():
        match = re.search(rf"{label}(?P<day>\d{{1,2}})日", message)
        if not match:
            continue
        target_year, target_month = _shift_month(base_date.year, base_date.month, offset)
        day = int(match.group("day"))
        value, adjusted = _safe_format_date(target_year, target_month, day)
        note = "日付を相対表現から推定" if not adjusted else "存在しない日付のため月末に補正"
        return DateResult(value, inferred=True, note=note)
    return None


def _match_month_day(message: str, base_date: date) -> Optional[DateResult]:
    patterns = [
        r"(?P<month>\d{1,2})/(?P<day>\d{1,2})",
        r"(?P<month>\d{1,2})月(?P<day>\d{1,2})日",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if not match:
            continue
        month = int(match.group("month"))
        day = int(match.group("day"))
        year = base_date.year
        candidate, adjusted = _safe_format_date(year, month, day)
        if candidate < base_date.isoformat():
            year += 1
            candidate, adjusted = _safe_format_date(year, month, day)
        note = "年が明示されていないため直近の年を推定"
        if adjusted:
            note = "存在しない日付のため月末に補正"
        return DateResult(candidate, inferred=True, note=note)
    return None


def _match_day_only(message: str, base_date: date) -> Optional[DateResult]:
    match = re.search(r"(?<!\d)(?P<day>\d{1,2})日(?!\d)", message)
    if not match:
        return None
    day = int(match.group("day"))
    year = base_date.year
    month = base_date.month
    candidate, adjusted = _safe_format_date(year, month, day)
    if candidate < base_date.isoformat():
        year, month = _shift_month(year, month, 1)
        candidate, adjusted = _safe_format_date(year, month, day)
    note = "月が明示されていないため直近の月を推定"
    if adjusted:
        note = "存在しない日付のため月末に補正"
    return DateResult(candidate, inferred=True, note=note)


def _shift_month(year: int, month: int, offset: int) -> Tuple[int, int]:
    total = year * 12 + (month - 1) + offset
    new_year = total // 12
    new_month = total % 12 + 1
    return new_year, new_month


def _safe_format_date(year: int, month: int, day: int) -> Tuple[str, bool]:
    try:
        return _format_date(year, month, day), False
    except ValueError:
        last_day = calendar.monthrange(year, month)[1]
        return _format_date(year, month, last_day), True


def _format_date(year: int, month: int, day: int) -> str:
    return date(year, month, day).isoformat()
