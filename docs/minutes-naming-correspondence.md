# Minutes Workflow 命名対応表（現状整理）

## 目的

minutes workflow 周辺で使われている語彙（workflow / step id / skill / backend / frontend / API endpoint）を1つの表に集約し、今後の rename の判断基準にする。

> **方針（今回）**: 大規模 rename は行わず、現状の差分を可視化するドキュメント整備に留める。

---

## Canonical name 方針（暫定）

今後の統一軸として、以下を **canonical name** とする。

1. **Workflow 名**: `meeting_minutes_workflow`（workflow YAML の `name` を正）
2. **Step 名**: `transcript_input` / `transcribe` / `draft` / `review` / `export`（workflow YAML の `steps[].id` を正）
3. **Skill 名**: `minutes-*`（kebab-case、`SKILL.md` の `name` を正）
4. **Backend クラス名**: `Minutes*Skill` / `WorkflowOrchestrator`（Python クラス名を正）
5. **Frontend 状態名**: API の `JobStatus` に合わせ、`WAITING_FOR_REVIEW` / `COMPLETED` を正。`CREATED` / `DRAFTING` はフロント内部状態として扱う。
6. **API endpoint 名**: Backend 実装済みの `/minutes/jobs*` を正。

---

## 命名対応表（minutes workflow 優先）

| Workflow 名 | Step id | Skill 名 (canonical) | Backend クラス名 | Frontend 状態名 / 表示 | API endpoint 名 | 備考 |
|---|---|---|---|---|---|---|
| `meeting_minutes_workflow` | `transcript_input` | `minutes-workflow` | `WorkflowOrchestrator`（入力分岐制御） | `CREATED`（入力待ち） | `POST /minutes/jobs`（`input_type=transcript`） | Step としては「入力取り込み」。backend 側で専用 skill クラスは未分離。 |
| `meeting_minutes_workflow` | `transcribe` | `minutes-transcribe` | `MinutesTranscribeSkill` | `DRAFTING`（処理中） | `POST /minutes/jobs`（`input_type=audio`） | audio 入力時のみ実行。 |
| `meeting_minutes_workflow` | `draft` | `minutes-draft` | `MinutesDraftSkill` | `DRAFTING`（処理中） | `POST /minutes/jobs` | 候補作成フェーズ。 |
| `meeting_minutes_workflow` | `review` | `minutes-review` | `MinutesReviewSkill` | `WAITING_FOR_REVIEW`（修正指示待ち） | `POST /minutes/jobs/{job_id}/review` | approve で完了へ、指示ありで再候補化。 |
| `meeting_minutes_workflow` | `export` | `minutes-export-word` | `MinutesExportWordSkill` | `COMPLETED`（※現在 FE 未定義） | `POST /minutes/jobs/{job_id}/review` 内で実行後に完了 | export 専用 endpoint ではなく review 完了時に実行。 |

---

## 用語差分（現状の命名ゆれ）

### 1) API 呼び出し名の不一致

- Frontend は `/api/create_entry` と `/api/create_entry/stream` を使用。
- Backend 実装は `/minutes/jobs`, `/minutes/jobs/{job_id}/review`, `/minutes/jobs/{job_id}`。
- したがって「minutes workflow の canonical API 名」は `/minutes/jobs*` と定義する。

### 2) Status 語彙の層間差

- Backend `JobStatus`: `WAITING_FOR_REVIEW`, `COMPLETED`。
- Frontend `STATUS`: `CREATED`, `DRAFTING`, `WAITING_FOR_REVIEW`。
- `CREATED` / `DRAFTING` は UI 制御上のローカル状態、`WAITING_FOR_REVIEW` / `COMPLETED` はドメイン状態と切り分ける。

### 3) Skill 名とクラス名の表記差

- Skill: `minutes-draft`（kebab-case）
- Class: `MinutesDraftSkill`（PascalCase）
- 表記ルールとして「仕様/設定は kebab-case、実装クラスは PascalCase」を canonical とする。

---

## 今後の rename 候補（優先度順）

1. Frontend API 名を `create_entry*` から `minutes/jobs*` 系へ寄せる。
2. Frontend 状態に `COMPLETED` を追加し、backend status と 1:1 にマッピングする。
3. `transcript_input` step の責務を明確化し、必要なら対応 skill（例: `minutes-input`）を追加。
4. SSE の phase 名（`PHASE*`）を minutes workflow の step id と関連づけるか、別ドメイン語彙として分離明記する。

