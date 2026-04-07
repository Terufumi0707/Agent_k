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
- `workflows` は backend コンテナに read-only マウントしています。
- 生成物は `./artifacts` に出力されます。
