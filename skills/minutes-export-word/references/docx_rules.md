# DOCX Export Rules

- 出力ファイル名は `{job_id}.docx`。
- `artifacts/` 配下に保存する。
- 見出し順は company format の sections 順。
- ファイル作成失敗時はエラー内容を呼び出し元に返す。
