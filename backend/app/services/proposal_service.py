from __future__ import annotations

from app.models.proposal_api_models import ProposalRequest, ProposalResponse


class ProposalService:
    """Minimal proposal-drafting service."""

    def create_proposal(self, request: ProposalRequest) -> ProposalResponse:
        title = f"{request.theme} 提案書（ドラフト）"
        constraints_line = "、".join(request.constraints) if request.constraints else "特になし"
        audience_line = request.audience or "関係者一同"

        summary = (
            f"目的: {request.objective}。"
            f"対象: {audience_line}。"
            f"制約: {constraints_line}。"
            "本ドラフトをたたき台として詳細化してください。"
        )

        sections = [
            "1. 背景と課題",
            "2. 提案内容",
            "3. 期待効果",
            "4. 実行計画",
            "5. リスクと対策",
        ]
        return ProposalResponse(title=title, summary=summary, sections=sections)
