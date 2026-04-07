# Minutes Workflow Agent

## Docker Compose での開発起動

frontend / backend を同時に起動するには、リポジトリルートで以下を実行します。

```bash
docker compose up --build
```

### 起動後のアクセス先

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## コンテナ間通信の構成

- `frontend` と `backend` は同じ Docker Compose ネットワーク上で起動します。
- frontend の開発サーバ (Vite) で `/api` を `http://backend:8000` へプロキシしています。
- フロントエンドコードは `VITE_API_BASE_PATH=/api` を使って API を呼び出すため、ブラウザからは service 名を意識せずに利用できます。

## 主な環境変数

- Frontend
  - `VITE_API_BASE_PATH` (default: `/api`)
- Backend
  - `PROJECT_ROOT` (default: `/app` in compose)

## 補足

- backend は `0.0.0.0:8000` で listen します。
- workflow / format YAML は `backend/workflows/` を実行時 truth source として管理します。
- 生成物は `./artifacts` に出力されます。

## Workflow YAML の truth source

- 実行時に backend が参照する workflow 定義は `backend/workflows/meeting_minutes_workflow.yaml` です。
- 実行時に backend が参照する format 定義は `backend/workflows/company_minutes_format.yaml` です。
- `skills/` 配下の YAML・記述は運用ドキュメント／テンプレート用途であり、実行時定義としては読み込みません。
