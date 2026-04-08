"""ローカル開発向けの直接設定。

必要な場合は、このファイルを直接編集して値を設定してください。
環境変数が設定されている場合は、そちらが優先されます。
"""

GEMINI_API_KEY = ""
# ↑ ここに API キーを直接設定してください（例: "AIza..."）。
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TIMEOUT_SECONDS = "120"

WHISPER_MODEL_SIZE = "small"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
