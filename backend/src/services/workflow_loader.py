from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOWS_DIR = Path(__file__).resolve().parents[2] / "workflows"
DEFAULT_WORKFLOW_PATH = WORKFLOWS_DIR / "meeting_minutes_workflow.yaml"
DEFAULT_FORMAT_PATH = WORKFLOWS_DIR / "company_minutes_format.yaml"


class WorkflowLoader:
    """YAML で管理されたワークフロー設定を読み込むローダー。"""

    def __init__(self, workflow_path: Path, format_path: Path) -> None:
        self.workflow_path = workflow_path
        self.format_path = format_path

    @classmethod
    def from_default_paths(cls) -> "WorkflowLoader":
        return cls(
            workflow_path=DEFAULT_WORKFLOW_PATH,
            format_path=DEFAULT_FORMAT_PATH,
        )

    def load_workflow(self) -> dict:
        # ワークフロー全体の手順定義を取得する。
        return yaml.safe_load(self.workflow_path.read_text(encoding="utf-8"))

    def load_company_format(self) -> dict:
        # 出力する議事録フォーマット（社内標準）を取得する。
        return yaml.safe_load(self.format_path.read_text(encoding="utf-8"))
