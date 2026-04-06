---
name: minutes-workflow
description: Orchestrate meeting minutes workflow steps and branching by input type (audio vs transcript).
---

# minutes-workflow

## 使うタイミング
- YAML workflow の step 順序を解釈し、実行計画を組み立てるとき。

## 入出力契約
- 入力: `input_type`, `audio_path?`, `transcript?`
- 出力: `plan`（実行 step 配列）, `state`

## 標準フロー
1. `references/routing_rules.md` に従って入力種別を判定。
2. `scripts/` 配下のオーケストレーション実装で step 実行計画を生成。
3. `input_type=audio` なら `transcribe` を含める。
4. `input_type=transcript` なら `transcribe` をスキップする。

## 実装方針
- step 定義は workflow YAML を唯一の truth source にする。
- 分岐条件は `references/routing_rules.md` と同期させる。

## 追加リソース
- 例: `examples/workflow_input_audio.json`, `examples/workflow_output_audio.json`
