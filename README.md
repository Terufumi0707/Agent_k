# 日程変更の受付AIエージェント（初期フェーズ）

PoC用途として、4プロセス構成（frontend / backend / api / mcp-order-lookup）のAIエージェントをローカルで動作させるためのサンプルです。

## ディレクトリ構成

```
frontend/                # Vue3 + Vite
backend/                 # FastAPI + LangGraph
api/                     # FastAPI (業務システムモック)
mcp_order_lookup_server/ # MCPサーバー（apiへの照会を中継）
```

## 環境変数

| 変数名 | 用途 | デフォルト |
| --- | --- | --- |
| SYSTEM_API_BASE_URL | backend -> api の接続先 | http://localhost:8001 |
| HTTP_TIMEOUT_SECONDS | backend の API タイムアウト | 5 |
| ORDER_LOOKUP_MCP_BASE_URL | backend -> MCP の接続先 | http://mcp-order-lookup:9000/mcp（Compose時） |
| VITE_BACKEND_BASE_URL | frontend -> backend の接続先 | http://localhost:8000（開発時） |
| VITE_AUTH0_DOMAIN | Auth0テナントドメイン（SPA設定） | your-tenant.us.auth0.com |
| VITE_AUTH0_CLIENT_ID | Auth0アプリのClient ID（SPA） | your-client-id |
| VITE_AUTH0_REDIRECT_URI | Auth0ログイン後のリダイレクト先 | http://localhost:5173 |
| GEMINI_API_BASE_URL | backend -> Gemini API の接続先 | https://generativelanguage.googleapis.com/v1beta |
| GEMINI_API_KEY | Gemini API の認証キー | (未設定) |
| GEMINI_MODEL | 利用する Gemini モデル名 | gemini-2.5-flash |
| GEMINI_TIMEOUT_SECONDS | Gemini API タイムアウト（最大60秒） | 60 |

## 起動方法

### 事前準備（PowerShell / Linux）

Gemini 2.5 Flash（無料で利用できるモデル）を前提に、API キーとモデル名を環境変数で設定します。

#### PowerShell

```
$env:GEMINI_API_KEY="your-api-key"
$env:GEMINI_MODEL="gemini-2.5-flash"
```

### 1. Docker Compose で全サービス（frontend / backend / api / mcp-order-lookup）を起動

Docker Compose で `frontend` / `backend` / `api` / `mcp-order-lookup` をまとめて起動します。`docker-compose.yml` では `GEMINI_API_KEY` がプレースホルダー (`your-api-key`) になっているため、そのままだと LLM 応答は空文字になります。

環境変数を使わずコードに直接書く場合は `backend/app/settings.py` の `GEMINI_API_KEY_CODE` に実キーを設定してください（検証用途のみ推奨）。

```
docker compose up --build
```

起動後のアクセス先:

- frontend: `http://localhost:5173`
- backend: `http://localhost:8000`
- api: `http://localhost:8001`
- mcp-order-lookup: `http://localhost:9000/mcp`

> **注意:** セッションは FastAPI プロセス内のインメモリ保持です。`backend` は `--workers 1` 前提で起動しています。再起動するとセッションは消えます。

#### .env での環境変数設定（任意）

Docker Compose が自動で読み込む `.env` を使う場合は、リポジトリ直下に作成してください。

```
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-2.5-flash
```

### 2. フロントエンドをローカル開発モードで単独起動したい場合（任意）

```
cd frontend
npm install
npm run dev
```

> **注意:** 本番やHTTPS環境でフロントエンドとバックエンドを別オリジンで動かす場合は、`VITE_BACKEND_BASE_URL` を必ず設定してください。未設定の場合は開発時のみ `http://localhost:8000`、それ以外は現在のオリジンを使用します。

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

Gemini API を利用する場合は、ローカルPCの環境変数に `GEMINI_API_KEY` を設定し、必要に応じて `GEMINI_MODEL` を指定してください（本 README では無料で利用できる Gemini 2.5 Flash を想定しています）。未設定または `your-api-key` などのプレースホルダの場合は従来の正規表現解析のみで処理します。API の利用料金やレート制限は提供元の規約に従ってください。

## テスト

```
cd backend
pytest
```

## トラブルシューティング

### Windows で `numpy` のビルドエラーが出る場合

`pip install -r requirements.txt` 実行時に `numpy` のビルドエラーが出る場合、Python のバージョンや `pip` の状態によってホイールが取得できず、ソースビルドが走って失敗している可能性があります。以下の手順を試してください。

1. **Python 3.12 を利用する**（推奨）  
   `numpy` のホイールが利用できる Python 3.12 で仮想環境を作成してください。

2. **pip をアップグレードする**  
   ```
   python -m pip install --upgrade pip
   ```

3. **ホイールの利用を強制する**（必要に応じて）  
   ```
   pip install --only-binary=:all: -r requirements.txt
   ```

それでも解消しない場合は、Visual Studio Build Tools をインストールして C/C++ コンパイラを利用可能にする必要があります。


## Auth0（OIDC + PKCE）設定メモ

本フロントエンドは `@auth0/auth0-vue` を使った Universal Login を前提にしています。Docker Compose 起動時は `VITE_AUTH0_*` を環境変数で渡してください。

Auth0ダッシュボードの SPA 設定では次を登録してください。

- Allowed Callback URLs: `http://localhost:5173`
- Allowed Logout URLs: `http://localhost:5173`
- Allowed Web Origins: `http://localhost:5173`

バックエンド側を保護する場合は、API で Access Token（issuer / audience / exp）を検証してください。
