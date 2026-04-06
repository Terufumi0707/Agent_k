# Meeting Minutes Workflow Agent Backend

## 概要
音声または文字起こしテキストを入力として受け、YAML定義ワークフローに従って議事録候補生成、HITLレビュー、Word (.docx) 出力までを行う FastAPI バックエンドです。

## アーキテクチャ
- `api/controllers`: 薄い HTTP エンドポイント
- `api/schemas`: Request/Response スキーマ
- `orchestrators`: ステップ実行制御・状態遷移
- `services`: Whisper / Draft生成 / Exporter などの業務ロジック
- `agents/runners`: ステップ単位の実行ユニット
- `workflows/definitions`: YAMLワークフロー
- `workflows/formats`: 会社固有フォーマット定義
- `repositories`: インメモリ永続層
- `domain`: entity / enum

## Gemini 接続設定（必須）
以下を環境変数に設定してください。

- `GEMINI_API_KEY` : Gemini APIキー（必須）
- `GEMINI_MODEL` : 既定 `gemini-2.5-flash`
- `GEMINI_API_BASE_URL` : 既定 `https://generativelanguage.googleapis.com/v1beta`
- `GEMINI_TIMEOUT_SECONDS` : 既定 `60`

`LlmClient` は Gemini `generateContent` API を呼び出し、JSON構造で議事録候補を受け取ります。

## 起動
```bash
cd backend
pip install -r requirements.txt
export GEMINI_API_KEY="your-api-key"
uvicorn src.main:app --reload --port 8000
```

## API
- `POST /jobs`
- `GET /jobs/{job_id}`
- `GET /jobs/{job_id}/candidates`
- `POST /jobs/{job_id}/feedback`
- `POST /jobs/{job_id}/approve`
- `GET /jobs/{job_id}/artifact`

## ダミー実装
- Whisper呼び出しはスタブ (`WhisperService`)

※ LLM は Gemini 接続の実装済みです。実運用時は必要に応じて認証・監査・リトライ戦略を強化してください。
