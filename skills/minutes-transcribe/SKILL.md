---
name: minutes-transcribe
description: Convert meeting audio into transcript text (PoC uses deterministic stub; production can switch to Whisper).
---

# minutes-transcribe

## 使うタイミング
- 入力が音声 (`audio_path`) のときに transcript を作成するとき。

## 入出力契約
- 入力: `audio_path`
- 出力: `transcript`

## 標準フロー
1. `references/transcription_modes.md` で PoC/本番モードの差分を確認。
2. `scripts/` 配下の実装（PoC では stub / 本番では Whisper）で transcript JSON を生成。
3. Whisper 実装へ差し替える場合も、出力キーは `transcript` を維持。

## 実装方針
- PoC では再現性重視（同入力→同出力）。
- 将来 Whisper 化しても I/O 契約は不変。

## 追加リソース
- 例: `examples/transcribe_input_example.json`, `examples/transcribe_output_example.json`
