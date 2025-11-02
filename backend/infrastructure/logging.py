"""バックエンドのログ出力を設定するためのユーティリティ。"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterable


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
LOG_FILE_NAME = "backend.log"
MAX_LOG_BYTES = 1_000_000
BACKUP_COUNT = 3


def _has_handler(handlers: Iterable[logging.Handler], log_path: Path) -> bool:
    """指定したパスのハンドラーが既に登録済みなら ``True`` を返す。"""

    for handler in handlers:
        if isinstance(handler, RotatingFileHandler) and getattr(
            handler, "baseFilename", None
        ) == str(log_path):
            return True
    return False


def configure_logging(level: int = logging.INFO) -> Path:
    """アプリ全体のロギング設定を初期化してログファイルを生成する。

    バックエンドの構造化ログを ``backend/logs/backend.log`` へ出力しつつ、
    uvicorn 標準の標準出力ログも維持する。uvicorn 系のロガーには
    propagate を有効化し、アクセスログとアプリログの両方が同じ
    ハンドラー設定に従うようにする。

    Parameters
    ----------
    level:
        ルートロガーへ適用するログレベル。デフォルトは ``logging.INFO`` で、
        過度に冗長にならず実用的な情報を得られる設定。

    Returns
    -------
    Path
        生成したログファイルのパス。呼び出し側で起動ログなどに表示できる。
    """

    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / LOG_FILE_NAME

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not _has_handler(root_logger.handlers, log_path):
        file_handler = RotatingFileHandler(
            log_path, maxBytes=MAX_LOG_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(file_handler)

    # uvicorn 系ロガーのログもルートロガーへ伝播させ、
    # ローテーションするファイルハンドラーでまとめて出力できるようにする。
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(logger_name).propagate = True

    return log_path


__all__ = ["configure_logging"]

