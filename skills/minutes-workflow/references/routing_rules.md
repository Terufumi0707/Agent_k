# Routing Rules

- `input_type=audio` の場合は transcribe step を実行する。
- `input_type=transcript` の場合は transcribe step をスキップする。
- どちらも最終的に `draft -> review -> export` を実行する。
