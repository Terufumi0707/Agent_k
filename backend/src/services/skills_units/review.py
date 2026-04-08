from __future__ import annotations

from typing import Any


class MinutesReviewSkill:
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        print(
            "[MinutesReviewSkill.run] invoked: "
            f"selected_index={payload.get('selected_index')}, action={payload.get('action')}",
            flush=True,
        )
        # レビュー対象の候補と指示内容を受け取り、承認/差し戻しを判定する。
        candidates = payload["candidates"]
        selected_index = payload["selected_index"]
        instruction = (payload.get("instruction") or "").strip()
        action = (payload.get("action") or "").strip().lower()
        base = candidates[selected_index]
        if not action:
            raise ValueError("action is required")
        if action == "revise":
            if not instruction:
                raise ValueError("instruction is required when action is revise")
            # 差し戻し時は元候補をコピーし、レビュー内容を追記した改訂版を返す。
            revised = dict(base)
            revised["レビュー反映"] = instruction
            print("[MinutesReviewSkill.run] returning revise result", flush=True)
            return {"approved": False, "revised_candidate": revised}
        if action == "approve":
            print("[MinutesReviewSkill.run] returning approve result", flush=True)
            return {"approved": True, "final_minutes": base}
        raise ValueError(f"unsupported review action: {action}")
