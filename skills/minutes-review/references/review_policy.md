# Review Policy

- `approve` の場合は選択候補をそのまま確定する。
- 修正時は元候補を保持し、`revision_note` に差分意図を残す。
- 範囲外 index は即時エラーにして誤承認を防ぐ。
