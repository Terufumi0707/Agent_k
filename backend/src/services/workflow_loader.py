from __future__ import annotations

from pathlib import Path

import yaml


class WorkflowLoader:
    def __init__(self, workflow_path: Path, format_path: Path) -> None:
        self.workflow_path = workflow_path
        self.format_path = format_path

    def load_workflow(self) -> dict:
        return yaml.safe_load(self.workflow_path.read_text(encoding="utf-8"))

    def load_company_format(self) -> dict:
        return yaml.safe_load(self.format_path.read_text(encoding="utf-8"))
