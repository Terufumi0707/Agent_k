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
- backend Docker イメージには音声デコード用に `ffmpeg` を同梱しています（faster-whisper 用）。
- ブラウザで選択した `.mp3` / `.mp4` は `/minutes/uploads/audio` で backend 側へ自動アップロードされ、保存先パスが `audio_path` としてジョブ作成に使われます。

### 停止

```bash
docker compose down
```


### Docker での音声文字起こし検証

Docker でも `faster-whisper` の検証が可能です。`backend` コンテナから参照できるパスを `audio_path` に指定してください。対応形式は `.mp3` と `.mp4` のみです。

1. ホスト側の `./artifacts` に音声ファイルを配置（例: `./artifacts/meeting.mp3`）
2. `docker compose up --build` で起動
3. 以下を実行（`/app/artifacts` は `./artifacts` がマウントされています）

```bash
curl -X POST http://localhost:8000/minutes/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "input_type": "audio",
    "audio_path": "/app/artifacts/meeting.mp3"
  }'
```

> 注: `docker-compose.yml` では `./artifacts:/app/artifacts` をマウントしているため、`audio_path` はコンテナ内パスで指定する必要があります。

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
# faster-whisper (PoC 推奨設定。未指定時も同じ値を使用)
export WHISPER_MODEL_SIZE="small"
export WHISPER_DEVICE="cpu"
export WHISPER_COMPUTE_TYPE="int8"
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


---

## 6. 音声文字起こし（faster-whisper PoC）

backend では `faster-whisper` を使って、`input_type=audio` の場合に音声ファイルから文字起こしを実行します。
文字起こし結果は既存の議事メモ生成フロー（draft/review）へそのまま渡されます。

### 6-1. 依存関係

- `backend/requirements.txt` に `faster-whisper` を追加済み
- セットアップは `pip install -r backend/requirements.txt` のみで OK

### 6-2. 設定値（環境変数）

- `WHISPER_MODEL_SIZE`（default: `small`）
- `WHISPER_DEVICE`（default: `cpu`）
- `WHISPER_COMPUTE_TYPE`（default: `int8`）

### 6-3. 実行例（音声入力）

backend 起動後、`audio_path` にローカルの音声ファイルパスを指定して実行します。

```bash
curl -X POST http://localhost:8000/minutes/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "input_type": "audio",
    "audio_path": "/absolute/path/to/meeting.mp3"
  }'
```

成功時はレスポンスの `transcript` に文字起こし済みテキストが入り、既存の候補生成結果（`candidates`）も返ります。

### 6-4. 注意点

- 本実装は PoC のため **CPU 前提** です。
- 初回実行時は Whisper モデル（`small`）のダウンロードが発生する場合があります。
- 長時間音声は処理に時間がかかります。
- `audio_path` のファイルが存在しない場合はエラーになります。
- 対応する音声形式は `.mp3` / `.mp4` のみです。
