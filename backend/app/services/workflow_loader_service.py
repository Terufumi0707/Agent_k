from pathlib import Path

import yaml


class WorkflowLoaderService:
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    def load(self, workflow_name: str) -> dict:
        path = self.base_path / f"{workflow_name}.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def load_format(self, format_name: str, format_base_path: Path) -> dict:
        path = format_base_path / f"{format_name}.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))
