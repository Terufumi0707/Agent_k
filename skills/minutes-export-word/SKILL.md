---
name: minutes-export-word
description: Export approved final meeting minutes into a .docx artifact with deterministic filename and section ordering.
---

# minutes-export-word

## 使うタイミング
- 承認済み `final_minutes` をユーザー共有用の `.docx` に変換するとき。

## 入出力契約
- 入力: `job_id`, `final_minutes`
- 出力: `artifact_path`

## 標準フロー
1. `references/docx_rules.md` で出力ルール（見出し順・ファイル名）を確認。
2. `scripts/` 配下のエクスポート実装（環境ごとに配置）で `artifacts/{job_id}.docx` を作成。
3. 作成後にファイル存在確認を行い `artifact_path` を返す。

## 実装方針
- 見出し順は `company_format` の定義順に合わせる。
- 出力失敗時は例外を握り潰さず、原因を明示する。

## 追加リソース
- 例: `examples/export_input_example.json`, `examples/export_output_example.json`
