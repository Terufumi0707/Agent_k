# 日程変更の受付AIエージェント（初期フェーズ）

PoC用途として、3プロセス構成のAIエージェントをローカルで動作させるためのサンプルです。

## ディレクトリ構成

```
frontend/   # Vue3 + Vite
backend/    # FastAPI + LangGraph
api/        # FastAPI (業務システムモック)
```

## 環境変数

| 変数名 | 用途 | デフォルト |
| --- | --- | --- |
| SYSTEM_API_BASE_URL | backend -> api の接続先 | http://localhost:8001 |
| HTTP_TIMEOUT_SECONDS | backend の API タイムアウト | 5 |
| VITE_BACKEND_BASE_URL | frontend -> backend の接続先 | http://localhost:8000 |
| GEMINI_API_BASE_URL | backend -> Gemini API の接続先 | https://generativelanguage.googleapis.com/v1beta |
| GEMINI_API_KEY | Gemini API の認証キー | (未設定) |
| GEMINI_MODEL | 利用する Gemini モデル名 | gemini-1.5-pro |
| GEMINI_TIMEOUT_SECONDS | Gemini API タイムアウト | 10 |

## 起動方法

### 1. 業務システム（api）

```
cd api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

### 2. AIエージェント（backend）

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
SYSTEM_API_BASE_URL=http://localhost:8001 uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

> **注意:** セッションは FastAPI プロセス内のインメモリ保持です。`--workers 1` 前提で起動してください。再起動するとセッションは消えます。

### 3. フロントエンド（frontend）

```
cd frontend
npm install
npm run dev
```

## デモ手順

1. フロントエンドの自然言語入力欄に「A-12345 工事種別: メイン回線_開通 希望日: 2026-02-10」などを入力して送信します。
2. 不足している項目がある場合は `need_more_info` となり、追加で必要な項目だけを自然文で追加入力します。
3. `fetch_current_order` を有効にすると、業務システムモックから参照情報が返ります。

## API 仕様（backend）

### POST /intake/start

初回入力を受け付け、`session_id` を発行します。

### POST /intake/next

`session_id` を指定して追加入力を送信します。存在しないセッションは `invalid_request` になります。

## LLM API について

Gemini API を利用する場合は、ローカルPCの環境変数に `GEMINI_API_KEY` を設定し、必要に応じて `GEMINI_MODEL` を指定してください。未設定の場合は従来の正規表現解析のみで処理します。API の利用料金やレート制限は提供元の規約に従ってください。

## テスト

```
cd backend
pytest
```
