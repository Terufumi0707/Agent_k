from __future__ import annotations

import json
from textwrap import dedent

BASE_MINUTES_INSTRUCTION = dedent(
    """\
    あなたは優秀な戦略コンサルタントです。添付したのはとあるクライアントとの会議のスクリプトですが、議事メモを作成してください。
    フォーマットは下記の通りでお願いします。
    ◆TODO（敬称略） ・[to-do 1]（[担当者]、[締切日]〆）
    ◆決定事項 ・[決定事項]
    """
).strip()

OUTPUT_REQUIREMENTS_TEMPLATE = dedent(
    """\
    出力要件:
    1) 候補を{num_candidates}件作成する
    2) 必ずJSONのみを返す（説明文なし）
    3) JSONスキーマ: {{"candidates":[{{"content":{{"<section>":["..."]}}}}]}}
    4) 各セクションは配列で返す
    5) TODOセクションには可能な限り 担当/期限/内容 を含める
    6) 下記セクションを必ず含める
    {section_instructions}
    """
).strip()


def build_minutes_prompt(
    transcript: str,
    sections: list[str],
    num_candidates: int,
    feedback: str | None = None,
    base_draft: dict[str, object] | None = None,
) -> str:
    section_instructions = "\n".join(f"- {name}" for name in sections)
    output_requirements = OUTPUT_REQUIREMENTS_TEMPLATE.format(
        num_candidates=num_candidates,
        section_instructions=section_instructions,
    )
    review_block = _build_review_block(feedback=feedback, base_draft=base_draft)

    return (
        f"{BASE_MINUTES_INSTRUCTION}\n\n"
        f"{output_requirements}\n"
        f"{review_block}"
        f"会議スクリプト:\n{transcript}"
    )


def _build_review_block(feedback: str | None, base_draft: dict[str, object] | None) -> str:
    lines: list[str] = []
    if feedback:
        lines.append(f"修正指示: {feedback}")
    if base_draft:
        lines.append(f"修正元ドラフト(JSON): {json.dumps(base_draft, ensure_ascii=False)}")

    if not lines:
        return "\n"

    return "\n".join(lines) + "\n\n"
