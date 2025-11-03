# MCP 連携開発メモ

このドキュメントでは、backend から MCP サーバー経由で日程変更モックロジックを呼び出す最小構成の動作確認手順をまとめます。

## 前提条件

- Python 3.10 以上が利用可能であること。
- プロジェクトルート (`matchingApp/`) をカレントディレクトリとして操作すること。
- 依存ライブラリは `backend/requirements.txt` を使用してインストール済みであること。

## 起動手順

1. **MCP サーバーを起動する**

   ```bash
   cd matchingApp
   PYTHONPATH=. python -m mcp.schedule_server
   ```

   標準出力/エラーに `schedule MCP server started. waiting for requests...` などのログが表示されれば準備完了です。

2. **FastAPI バックエンドを MCP モードで起動する**

   別ターミナルで以下を実行します。

   ```bash
   cd matchingApp
   PYTHONPATH=. USE_MCP=1 uvicorn backend.api:app --reload --port 8000
   ```

   起動ログに `using MCPScheduleApiGateway` と `mcp_schedule_change_call ...` が出力されることを確認してください。

## 動作確認

1. **ヘルスチェック**

   ```bash
   curl -s http://localhost:8000/api/health
   ```

   `{"status":"ok"}` が返れば正常です。

2. **ワークフロー実行 (MCP 経由)**

   ```bash
   curl -s -X POST http://localhost:8000/api/workflows/select \
     -H 'Content-Type: application/json' \
     -d '{"workflowId":"schedule_change","decision":"proceed","message":"エントリID 0001 の日程変更をお願いします。2024年07月21日15:30に変更希望。理由: 社内調整のため。"}'
   ```

   レスポンスの `status` と `message` にモック API 由来の内容が含まれ、`message` 内に「日程変更のリクエストであると判断しました」「現在登録されている日程」「理由: 社内調整のため」などの文言が確認できます。

3. **フォールバック確認 (MCP 未使用)**

   MCP サーバーを停止するか、`USE_MCP` 環境変数を指定せずにバックエンドを起動します。

   ```bash
   cd matchingApp
   PYTHONPATH=. uvicorn backend.api:app --reload --port 8000
   ```

   上記の `curl` リクエストを再度実行し、従来のモック API 直接呼び出しでも同様のレスポンスが得られることを確認してください。

## 補足

- MCP サーバーおよびバックエンドは両方とも `PYTHONPATH=.` を設定してモジュール解決を行います。
- 異常系ではバックエンドは `status="error"` とエラーメッセージを返し、フロントエンド既存実装との互換性を保ちます。
