"""開発時に利用するモックAPIを提供するFastAPIアプリケーション。

エンドポイント一覧
-------------------
GET /healthz
    サービスの稼働状態を示すヘルスチェック結果を返す。
POST /chat
    ``message`` を受け取り、決定論的な返信を返すチャットAPIのモック。
POST /schedule-change
    スケジュール変更リクエストを受け取り、モックサービスによる判定結果を返す。
"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from backend.domain.schedule_change.entities import ScheduleChangeRequest

from .mock_backend_chat import mock_reply
from .schedule_change_service import handle_schedule_change_request


class ChatRequest(BaseModel):
    """チャットモックAPIが受け取るリクエストボディ。"""

    message: str


class ChatResponse(BaseModel):
    """チャットモックAPIが返却するレスポンスボディ。"""

    reply: str


class ScheduleChangePayload(BaseModel):
    """スケジュール変更モックAPIが受け取るリクエストボディ。"""

    entry_id: str
    prompt: str
    requester: Optional[str] = None
    reason: Optional[str] = None


class ScheduleChangeResult(BaseModel):
    """スケジュール変更モックAPIが返却するレスポンスボディ。"""

    status: str
    message: str


def create_app() -> FastAPI:
    """FastAPIアプリケーションインスタンスを生成して設定する。"""

    app = FastAPI(title="Mock Backend API", version="0.1.0")

    # ヘルスチェックAPI: サービスが稼働しているかを判定するために利用する。
    @app.get("/healthz")
    def healthcheck() -> dict[str, str]:
        """稼働状態を示すシンプルなヘルスチェックエンドポイント。"""

        return {"status": "ok"}

    # チャットAPI: 指定されたメッセージに対して決定論的な返信を返す。
    @app.post("/chat", response_model=ChatResponse)
    def chat(payload: ChatRequest) -> ChatResponse:
        """UI開発向けに決定論的な返信を返すチャットモック。"""

        return ChatResponse(reply=mock_reply(payload.message))

    # スケジュール変更API: モックサービスに処理を委譲して判定結果を返す。
    @app.post("/schedule-change", response_model=ScheduleChangeResult)
    def schedule_change(payload: ScheduleChangePayload) -> ScheduleChangeResult:
        """スケジュール変更リクエストをモックサービスに転送して判定結果を返す。"""

        request = ScheduleChangeRequest(
            entry_id=payload.entry_id,
            prompt=payload.prompt,
            requester=payload.requester,
            reason=payload.reason,
        )
        response = handle_schedule_change_request(request)
        return ScheduleChangeResult(status=response.status, message=response.message)

    return app


app = create_app()


__all__ = [
    "ChatRequest",
    "ChatResponse",
    "ScheduleChangePayload",
    "ScheduleChangeResult",
    "app",
    "create_app",
]
