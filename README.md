# matchingApp

フロントエンドを Streamlit から Vue.js に刷新し、FastAPI ベースのバックエンドと連携する構成に更新しました。以下の手順でローカル開発環境を立ち上げられます。

## ディレクトリ構成

- `frontend/` — Vite + Vue 3 を利用した SPA。Pinia で状態管理を行い、**すべてのデータ取得はバックエンド API 経由で行います**。
- `backend/` — LangGraph ワークフローを呼び出す FastAPI アプリケーション。`uvicorn` で起動し、フロントエンドからの `/api` リクエストを受け付けます。
- `mcp/` — MCP（Model Context Protocol）関連のコードを配置する予定の領域。今後の実装をここに追加します。
- `mock_api/` — バックエンドが外部サービスと連携する際のスタブ実装をまとめています。バックエンド内部からのみ参照します。

## セットアップ

### Python バックエンド

1. 依存関係をインストールします。
   ```bash
   pip install -r backend/requirements.txt
   ```
2. FastAPI アプリを起動します。
   ```bash
   python3 -m uvicorn backend.api:app --reload
   ```
3. バックエンドのログは `backend/logs/backend.log` にローテーション付きで保存されます。
   別ターミナルで以下を実行するとリアルタイムに確認できます。
   ```bash
   tail -f backend/logs/backend.log
   ```
4. ワークスペース一覧など UI で利用するデータはバックエンドの `/api/workspaces` 系エンドポイントが提供します。フロントエンドはバックエンド以外のサービスへ直接アクセスしません。

### Vue フロントエンド

1. 依存関係をインストールします。
   ```bash
   cd frontend
   npm install
   ```
2. 開発サーバーを起動します。
   ```bash
   npm run dev
   ```
3. ブラウザで `http://localhost:5173` にアクセスすると、Vue ベースの UI が表示されます。開発サーバーは `/api` へのリクエストを FastAPI にプロキシします。

### モック API

- `mock_api/mock_backend_chat.py` には、バックエンドから呼び出す簡易レスポンス生成ロジックが含まれています。フロントエンドは直接利用せず、必ずバックエンド経由で通信します。

### Backend API (モック)

バックエンドのワークフローからモック API を呼び出す場合は、`mock_api` 配下の FastAPI サーバーを起動してください。

```bash
pip install -r mock_api/requirements.txt  # まだインストールしていない場合
PYTHONPATH=. python3 -m uvicorn mock_api.server:app --reload --port 8001
```

> **Note:** `PYTHONPATH=.` を指定できない環境では、リポジトリルートを `sys.path` に追加するなどして `backend` モジュールを解決できるようにしてください。

## テスト

- Python 側: 適宜 `pytest` やユニットテストを実行してください。
- フロントエンド: Vite が提供する `npm run build` などを利用してビルド検証が可能です。

## ライセンス

このプロジェクトは MIT License の下で公開されています。
