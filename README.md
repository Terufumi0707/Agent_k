# matchingApp

フロントエンドを Streamlit から Vue.js に刷新し、FastAPI ベースのバックエンドと連携する構成に更新しました。以下の手順でローカル開発環境を立ち上げられます。

## ディレクトリ構成

- `baycurrent_ui_clean/frontend` — Vite + Vue 3 を利用した SPA。Pinia で状態管理を行い、バックエンド API と通信します。
- `baycurrent_ui_clean/src/backend` — LangGraph ワークフローを呼び出す FastAPI アプリケーション。`uvicorn` で起動します。

## セットアップ

### Python バックエンド

1. 依存関係をインストールします。
   ```bash
   pip install -r baycurrent_ui_clean/requirements.txt
   ```
2. FastAPI アプリを起動します。
   ```bash
   uvicorn backend.api:app --app-dir baycurrent_ui_clean/src --reload
   ```

### Vue フロントエンド

1. 依存関係をインストールします。
   ```bash
   cd baycurrent_ui_clean/frontend
   npm install
   ```
2. 開発サーバーを起動します。
   ```bash
   npm run dev
   ```
3. ブラウザで `http://localhost:5173` にアクセスすると、Vue ベースの UI が表示されます。開発サーバーは `/api` へのリクエストを FastAPI にプロキシします。

## テスト

- Python 側: 適宜 `pytest` やユニットテストを実行してください。
- フロントエンド: Vite が提供する `npm run build` などを利用してビルド検証が可能です。

## ライセンス

このプロジェクトは MIT License の下で公開されています。
