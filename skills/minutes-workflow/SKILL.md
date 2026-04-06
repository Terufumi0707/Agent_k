# minutes-workflow

## 役割
- YAML workflow の step 順序を解釈し、オーケストレーションする。
- 入力種別（audio/transcript）に応じて transcribe step を分岐する。

## 入力
- `input_type`
- `audio_path` or `transcript`

## 出力
- transcript
- draft candidates
- review 待ち状態
