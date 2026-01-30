from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from app.llm_client import generate_autonomous_question
from app.llm_prompts import build_autonomous_prompt

WORK_TYPE_CANONICAL = [
    "現地調査",
    "付帯工事",
    "アクセス工事",
    "導通工事",
    "事前配線",
    "宅内工事",
    "端末工事",
    "切替工事",
    "端末撤去",
    "コム撤去",
    "地域撤去",
    "ケーブル撤去",
    "PD撤去",
    "DF現調",
    "開通日",
]

WORK_TYPE_SYNONYMS = {
    "現調": "現地調査",
    "宅内": "宅内工事",
    "端末": "端末工事",
    "切り替え": "切替工事",
    "切替": "切替工事",
}


@dataclass
class WorkTypeEntry:
    name: str
    confidence: str


@dataclass
class DialogueState:
    a_number: Optional[str] = None
    work_types: List[WorkTypeEntry] = field(default_factory=list)
    date: Optional[str] = None
    date_inferred: bool = False
    overall_confidence: str = "low"
    history: List[Dict[str, str]] = field(default_factory=list)
    validation_errors: List[Dict[str, str]] = field(default_factory=list)

    def record_turn(self, role: str, message: str) -> None:
        self.history.append({"role": role, "message": message})


class RuleBasedValidator:
    def validate(self, state: DialogueState) -> Tuple[bool, List[Dict[str, str]]]:
        # 収集済み情報の整合性をルールベースで検証する。
        errors: List[Dict[str, str]] = []
        if state.a_number and not _is_valid_a_number(state.a_number):
            errors.append({"field": "a_number", "reason": "format_mismatch"})
        if state.work_types:
            invalid = [wt.name for wt in state.work_types if wt.name not in WORK_TYPE_CANONICAL]
            if invalid:
                errors.append({"field": "work_types", "reason": "invalid_category"})
        else:
            errors.append({"field": "work_types", "reason": "missing"})
        if state.date and not _is_valid_date(state.date):
            errors.append({"field": "date", "reason": "format_mismatch"})
        elif not state.date:
            errors.append({"field": "date", "reason": "missing"})
        if not state.a_number:
            errors.append({"field": "a_number", "reason": "missing"})
        return not errors, errors


class AutonomousAgent:
    def __init__(self) -> None:
        # 対話状態はセッション単位で保持する。
        self.state = DialogueState()
        self.validator = RuleBasedValidator()

    def initial_prompt(self) -> str:
        return (
            "工事に関するご相談ですね。"
            "A番号・工事種別・日程のうち、分かるところから教えてください。"
        )

    def handle_user_input(self, message: str, base_date: Optional[date] = None) -> Dict[str, object]:
        # ①ユーザー入力の記録と抽出
        self.state.record_turn("user", message)
        self._extract_from_message(message, base_date)

        # ②不足項目がある場合は質問を生成
        if not self._has_all_fields():
            question = self._generate_question(message)
            self.state.record_turn("assistant", question)
            return {"status": "need_more_info", "question": question}

        # ③必要項目が揃ったらルールベース検証
        is_valid, errors = self.validator.validate(self.state)
        if is_valid:
            # ④問題なければ最終出力を返す
            self.state.overall_confidence = _estimate_overall_confidence(self.state)
            result = {
                "a_number": self.state.a_number,
                "work_types": [
                    {"name": wt.name, "confidence": wt.confidence} for wt in self.state.work_types
                ],
                "date": self.state.date,
                "date_inferred": self.state.date_inferred,
                "overall_confidence": self.state.overall_confidence,
            }
            return {"status": "completed", "result": result}

        self.state.validation_errors = errors
        # ④がNGの場合はvalidation_errorsを添えてLLMに再質問を生成させる
        question = self._generate_question(message, errors)
        self.state.record_turn("assistant", question)
        return {"status": "need_more_info", "question": question}

    def _has_all_fields(self) -> bool:
        return bool(self.state.a_number and self.state.work_types and self.state.date)

    def _extract_from_message(self, message: str, base_date: Optional[date]) -> None:
        if not self.state.a_number:
            a_number = _extract_a_number(message)
            if a_number:
                self.state.a_number = a_number
        if not self.state.work_types:
            work_types = _extract_work_types(message)
            if work_types:
                self.state.work_types = work_types
        if not self.state.date:
            normalized, inferred = _extract_date(message, base_date)
            if normalized:
                self.state.date = normalized
                self.state.date_inferred = inferred

    def _generate_question(
        self, message: str, validation_errors: Optional[List[Dict[str, str]]] = None
    ) -> str:
        # LLMへ渡す入力（対話履歴・収集済み情報・検証結果）を組み立てる。
        payload = {
            "history": self.state.history,
            "current_state": {
                "a_number": self.state.a_number,
                "work_types": [
                    {"name": wt.name, "confidence": wt.confidence} for wt in self.state.work_types
                ],
                "date": self.state.date,
                "date_inferred": self.state.date_inferred,
            },
            "last_user_message": message,
            "validation_errors": validation_errors or [],
        }
        prompt = build_autonomous_prompt(payload)
        llm_result = generate_autonomous_question(prompt)
        if llm_result.get("question"):
            # LLMが補完的に抽出した情報があれば状態に反映。
            self._merge_llm_extraction(llm_result)
            return str(llm_result["question"])
        return _fallback_question(validation_errors or [], self.state)

    def _merge_llm_extraction(self, llm_result: Dict[str, object]) -> None:
        if not self.state.a_number and llm_result.get("a_number"):
            self.state.a_number = str(llm_result["a_number"])
        if not self.state.work_types and llm_result.get("work_types"):
            work_types: List[WorkTypeEntry] = []
            for item in llm_result.get("work_types") or []:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                confidence = item.get("confidence") or "medium"
                if name:
                    work_types.append(WorkTypeEntry(name=str(name), confidence=str(confidence)))
            if work_types:
                self.state.work_types = work_types
        if not self.state.date and llm_result.get("date"):
            date_value = str(llm_result["date"])
            self.state.date = date_value
            self.state.date_inferred = bool(llm_result.get("date_inferred"))


def _extract_a_number(message: str) -> Optional[str]:
    import re

    match = re.search(r"A\d{9}", message)
    return match.group(0) if match else None


def _extract_work_types(message: str) -> List[WorkTypeEntry]:
    work_types: List[WorkTypeEntry] = []
    for name in WORK_TYPE_CANONICAL:
        if name in message:
            work_types.append(WorkTypeEntry(name=name, confidence="high"))
    for synonym, canonical in WORK_TYPE_SYNONYMS.items():
        if synonym in message and canonical not in {wt.name for wt in work_types}:
            work_types.append(WorkTypeEntry(name=canonical, confidence="medium"))
    return work_types


def _extract_date(message: str, base_date: Optional[date]) -> Tuple[Optional[str], bool]:
    base = base_date or date.today()
    normalized, inferred = _normalize_date_string(message, base)
    if normalized:
        value, rolled = _normalize_date_value(normalized, base)
        return value, inferred or rolled
    return None, False


def _normalize_date_string(message: str, base: date) -> Tuple[Optional[str], bool]:
    import re

    match = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", message)
    if match:
        return (
            f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}",
            False,
        )
    match = re.search(r"(\d{1,2})[/-](\d{1,2})", message)
    if match:
        return (
            f"{base.year}-{int(match.group(1)):02d}-{int(match.group(2)):02d}",
            True,
        )
    if "今日" in message:
        return base.isoformat(), True
    if "明日" in message:
        return (base + timedelta(days=1)).isoformat(), True
    if "明後日" in message or "あさって" in message:
        return (base + timedelta(days=2)).isoformat(), True
    return None, False


def _normalize_date_value(value: str, base: date) -> Tuple[Optional[str], bool]:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None, False
    rolled = False
    if parsed < base:
        try:
            parsed = parsed.replace(year=parsed.year + 1)
            rolled = True
        except ValueError:
            return None, False
    return parsed.isoformat(), rolled


def _is_valid_a_number(value: str) -> bool:
    import re

    return bool(re.fullmatch(r"A\d{9}", value))


def _is_valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _estimate_overall_confidence(state: DialogueState) -> str:
    if not state.work_types or not state.date or not state.a_number:
        return "low"
    if state.date_inferred:
        return "medium"
    if any(wt.confidence != "high" for wt in state.work_types):
        return "medium"
    return "high"


def _fallback_question(
    validation_errors: List[Dict[str, str]], state: DialogueState
) -> str:
    # LLMが回答できない場合のフォールバック。ユーザーに不足項目を丁寧に確認する。
    if validation_errors:
        fields = [err.get("field") for err in validation_errors]
        if "a_number" in fields:
            return "念のため、今回の工事に紐づく番号をもう一度教えてください。"
        if "work_types" in fields:
            return "今回の工事種別を確認させてください。"
        if "date" in fields:
            return "日程について、少しだけ確認させてください。"
    if not state.a_number:
        return "念のため、今回の工事に紐づく番号を教えてください。"
    if not state.work_types:
        return "今回の工事種別を教えてください。"
    if not state.date:
        return "日程について、少しだけ確認させてください。"
    # ここまで来るのは稀だが、曖昧な場合の汎用確認。
    return "不足している情報を整理したいので、A番号・工事種別・日程のうち未共有の項目を教えてください。"
