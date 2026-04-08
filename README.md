# Minutes Workflow Agent

議事録作成ワークフローを、**Vue (frontend)** + **FastAPI (backend)** でローカル実行できるアプリです。

---

## 1. 前提条件

- Docker で実行する場合
  - Docker Engine
  - Docker Compose (`docker compose`)
- Docker を使わずに実行する場合
  - Python 3.11 以上（推奨）
  - Node.js 20 以上（推奨）
  - npm

---

## 2. Gemini API キーの準備（共通）

このアプリのドラフト生成では Gemini API を利用します。backend は `GEMINI_API_KEY` 環境変数を参照します。

### 2-1. API キー取得

1. Google AI Studio などで Gemini API キーを発行
2. 取得したキーを控える

### 2-2. 環境変数設定（例）

#### macOS / Linux (bash, zsh)

```bash
export GEMINI_API_KEY="your_api_key_here"
```

#### Windows PowerShell

```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

> 補足: 必要に応じて以下も設定可能です。
>
> - `GEMINI_MODEL`（default: `gemini-2.5-flash`）
> - `GEMINI_TIMEOUT_SECONDS`（default: `20`）

---

## 3. Docker で起動する

frontend / backend を同時に起動します。

```bash
docker compose up --build
```

### アクセス先

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000>

### Docker 実行時のポイント

- frontend は `/api` を `http://backend:8000` にプロキシします。
- ブラウザからは `/api` 経由で backend にアクセスします。
- 生成物（docx 等）は `./artifacts` に出力されます。

### 停止

```bash
docker compose down
```

---

## 4. Docker を使わずに起動する

backend と frontend をそれぞれ別ターミナルで起動します。

### 4-1. Backend 起動

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your_api_key_here"
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4-2. Frontend 起動

別ターミナルで実行:

```bash
cd frontend
npm install
VITE_BACKEND_BASE_URL=http://localhost:8000 VITE_API_BASE_PATH= npm run dev -- --host 0.0.0.0 --port 5173
```

### アクセス先

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000>

> `VITE_BACKEND_BASE_URL=http://localhost:8000` を指定すると、frontend から backend へ直接アクセスできます。`VITE_API_BASE_PATH` は空文字にしています（`/minutes/jobs` へ直接リクエスト）。

---

## 5. ワークフロー定義（truth source）

実行時に backend が参照する定義ファイル:

- `backend/workflows/meeting_minutes_workflow.yaml`
- `backend/workflows/company_minutes_format.yaml`

`skills/` 配下の YAML や記述はテンプレート/運用ドキュメント用途であり、実行時定義としては読み込みません。
