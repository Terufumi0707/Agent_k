# matchingApp

フロントエンドを Streamlit から Vue.js に刷新し、FastAPI ベースのバックエンドと連携する構成に更新しました。以下の手順でローカル開発環境を立ち上げられます。

## ディレクトリ構成

- `frontend/` — Vite + Vue 3 を利用した SPA。Pinia で状態管理を行い、バックエンド API と通信します。
- `backend/` — LangGraph ワークフローを呼び出す FastAPI アプリケーション。`uvicorn` で起動します。
- `mcp/` — MCP（Model Context Protocol）関連のコードを配置する予定の領域。今後の実装をここに追加します。
- `mock-api/` — フロントエンドとの疎通確認用に利用できるモック API 実装を配置します。

## セットアップ

### Python バックエンド

1. 依存関係をインストールします。
   ```bash
   pip install -r backend/requirements.txt
   ```
2. FastAPI アプリを起動します。
   ```bash
   uvicorn backend.api:app --reload
   ```

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

- `mock-api/mock_backend_chat.py` には、フロントエンドと組み合わせて動作確認を行う際に利用できる簡易レスポンス生成ロジックが含まれています。必要に応じて FastAPI 等のサーバー実装を追加してください。

## テスト

- Python 側: 適宜 `pytest` やユニットテストを実行してください。
- フロントエンド: Vite が提供する `npm run build` などを利用してビルド検証が可能です。

## ライセンス

このプロジェクトは MIT License の下で公開されています。
