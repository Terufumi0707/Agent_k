from __future__ import annotations

from pathlib import Path
from typing import Any


class MinutesTranscribeSkill:
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        # 実運用では音声認識結果を返す想定。現在はファイル名を含むダミー文字列を返す。
        audio_path = payload["audio_path"]
        filename = Path(audio_path).name
        return {"transcript": f"[whisper transcript:{filename}] 会議の要点、決定事項、担当タスク。"}
