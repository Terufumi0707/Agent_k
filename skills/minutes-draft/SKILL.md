---
name: minutes-draft
description: Generate 2-3 meeting-minutes draft candidates from transcript and company format, with optional feedback-based revision.
---

# minutes-draft

## 使うタイミング
- `transcript` と `company_format` から議事録案を複数作るとき。
- 既存案 (`base_draft`) をフィードバック (`feedback`) で改善するとき。

## 入出力契約
- 入力: `transcript`, `company_format`, `candidate_count`, `feedback?`, `base_draft?`
- 出力: `candidates` (配列)

## 標準フロー
1. `references/quality_checklist.md` を読み、必須セクションと品質観点を確認。
2. `assets/draft_prompt_template.md` をベースにドラフト生成指示を組み立てる。
3. `scripts/` 配下の実装（環境ごとに配置）を呼び出し、候補を JSON で出力する。
4. 生成後、候補ごとの重複や空欄をチェックする。

## 実装方針
- 候補間で表現の多様性を確保する。
- `company_format.sections[].required=true` は全候補で必ず充足。
- `feedback` がある場合は変更点を候補先頭に要約して反映する。

## 追加リソース
- 例: `examples/draft_input_example.json`, `examples/draft_output_example.json`
