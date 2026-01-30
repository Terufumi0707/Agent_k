from __future__ import annotations

import re
from typing import Dict, List, Optional

from app.llm_client import parse_message_with_gemini
from app.llm_prompts import gemini_extract_prompt
from app.models import WorkChange

IDENTIFIER_PATTERN = re.compile(r"[A-Z]{2}\d{10}", re.IGNORECASE)
WORK_CHANGE_PATTERN = re.compile(
    r"(?:工事種別|work_type)[:：]\s*(?P<work_type>[^,\n]+?)\s*"
    r"(?:,|\n| )+"
    r"(?:変更希望日|希望日|desired_date)[:：]\s*(?P<desired_date>\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)


def parse_message(message: Optional[str]) -> Dict:
    if not message:
        return {}

    parsed: Dict[str, object] = {}

    id_match = IDENTIFIER_PATTERN.search(message)
    if id_match:
        identifier = id_match.group(0)
        if re.search(r"(A番号|a番号)", message, re.IGNORECASE):
            parsed["a_number"] = identifier
        elif re.search(r"(エントリ|entry)", message, re.IGNORECASE):
            parsed["entry_id"] = identifier

    work_changes: List[WorkChange] = []
    for match in WORK_CHANGE_PATTERN.finditer(message):
        work_changes.append(
            WorkChange(
                work_type=match.group("work_type").strip(),
                desired_date=match.group("desired_date").strip(),
            )
        )

    if work_changes:
        parsed["work_changes"] = work_changes

    needs_llm = not parsed.get("a_number") and not parsed.get("entry_id")
    needs_llm = needs_llm or not parsed.get("work_changes")
    if needs_llm:
        llm_parsed = parse_message_with_llm(message)
        parsed = merge_parsed_results(parsed, llm_parsed)

    return parsed


def parse_message_with_llm(message: str) -> Dict[str, object]:
    prompt = gemini_extract_prompt(message)
    return parse_message_with_gemini(prompt)


def merge_parsed_results(primary: Dict[str, object], secondary: Dict[str, object]) -> Dict[str, object]:
    merged = dict(primary)
    for key, value in secondary.items():
        if key not in merged or not merged[key]:
            merged[key] = value
    return merged
