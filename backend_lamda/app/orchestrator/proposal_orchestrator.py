from __future__ import annotations

from app.models.entity.proposal_context import ProposalContext
from app.models.entity.proposal_result import ProposalResult
from app.models.request.proposal_create_request import ProposalCreateRequest
from app.models.response.proposal_create_response import ProposalCreateResponse
from app.service.proposal_service import ProposalService


class ProposalOrchestrator:
    def __init__(self, proposal_service: ProposalService) -> None:
        self.proposal_service = proposal_service

    async def create_proposal(self, request: ProposalCreateRequest) -> ProposalCreateResponse:
        # 1. request validation (Pydantic validation is already applied in request parsing)
        context = ProposalContext(**request.model_dump())

        # 2. Looker API
        looker_data = await self.proposal_service.fetch_looker_data(
            target_company=context.target_company,
            theme=context.theme,
        )

        # 3. Gemini prompt generation
        prompt = self._build_gemini_prompt(context=context, looker_data=looker_data)

        # 4. Gemini call
        gemini_summary = await self.proposal_service.run_gemini(prompt=prompt)

        # 5. GAS payload generation
        gas_payload = self._build_gas_payload(context=context, looker_data=looker_data, gemini_summary=gemini_summary)

        # 6. GAS API
        gas_result = await self.proposal_service.send_to_gas(payload=gas_payload)

        # 7. response formatting
        data = ProposalResult(looker_data=looker_data, gemini_summary=gemini_summary, gas_result=gas_result)

        # 8. return
        return ProposalCreateResponse(status="success", message="提案書の作成処理が完了しました。", data=data)

    def _build_gemini_prompt(self, context: ProposalContext, looker_data: dict) -> str:
        return (
            "あなたは提案書作成エージェントです。以下の情報をもとにJSONのみを返却してください。\n"
            "返却JSONキー: executive_summary, proposal_outline, key_messages, risks, next_actions\n"
            f"テーマ: {context.theme}\n"
            f"提案先: {context.target_company}\n"
            f"背景: {context.background}\n"
            f"課題: {context.issues}\n"
            f"ゴール: {context.goal}\n"
            f"補足条件: {context.additional_requirements or 'なし'}\n"
            f"Lookerデータ: {looker_data}\n"
        )

    def _build_gas_payload(
        self,
        context: ProposalContext,
        looker_data: dict,
        gemini_summary: dict,
    ) -> dict:
        return {
            "theme": context.theme,
            "target_company": context.target_company,
            "background": context.background,
            "issues": context.issues,
            "goal": context.goal,
            "additional_requirements": context.additional_requirements,
            "analytics": looker_data,
            "summary": gemini_summary,
        }
