---
name: minutes-review
description: Present draft candidates, apply user correction instructions, and return either revised candidate or approved final minutes.
---

# minutes-review

## 使うタイミング
- 議事録候補を提示してユーザー承認 (`approve`) か修正指示を受けるとき。

## 入出力契約
- 入力: `candidates`, `selected_index`, `instruction`
- 出力: `revised_candidate` または `final_minutes`

## 標準フロー
1. `instruction` が `approve` 相当か判定。
2. `approve` の場合は選択候補を `final_minutes` として返す。
3. 修正指示の場合は `scripts/` 配下の実装で候補を 1 件追加生成。
4. `references/review_policy.md` に従い、変更点サマリーを付与して返却。

## 実装方針
- 候補の原文を保持し、変更箇所を明示。
- `selected_index` 範囲外は即時エラーにする。

## 追加リソース
- 例: `examples/review_input_example.json`, `examples/review_output_example.json`
